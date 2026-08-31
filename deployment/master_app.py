import sys
import os
import importlib

if getattr(sys, 'frozen', False):
    # PyInstaller execution
    os.environ['CUDA_HOME'] = os.path.join(sys._MEIPASS, 'cuda_toolkit')

# Fix for Windows Python 3.8+ DLL loading for CuPy
if os.name == 'nt':
    import glob
    import site
    for site_pkg in site.getsitepackages():
        for bin_dir in glob.glob(os.path.join(site_pkg, 'nvidia', '*', 'bin')):
            if os.path.isdir(bin_dir):
                os.add_dll_directory(bin_dir)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import ctypes
import matplotlib
matplotlib.use('Agg')

class ModuleIsolator:
    """ Context manager to isolate sys.path and sys.modules for sub-projects. """
    def __init__(self, target_dir):
        if getattr(sys, 'frozen', False):
            self.target_dir = os.path.abspath(os.path.join(sys._MEIPASS, target_dir))
        else:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.target_dir = os.path.abspath(os.path.join(root_dir, target_dir))
        self.colliding_modules = ['sweep_core', 'parameters', 'plotter', 'phase_diagram', 'full_bz_solver', 'solvers', 'app', 'main']
        self.saved_modules = {}
        self.old_path = []

    def __enter__(self):
        self.old_path = sys.path.copy()
        sys.path.insert(0, self.target_dir)
        
        for mod in self.colliding_modules:
            if mod in sys.modules:
                self.saved_modules[mod] = sys.modules.pop(mod)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.path = self.old_path
        
        for key in list(sys.modules.keys()):
            if key in self.colliding_modules:
                sys.modules.pop(key)
                
        sys.modules.update(self.saved_modules)


class MasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Physics Analyzer")

        # Top frame for global settings
        top_frame = ttk.Frame(root)
        top_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(top_frame, text="Output Folder:").pack(side='left')
        
        default_out = os.path.join(os.path.expanduser('~'), 'Desktop', 'Physics_Plots')
        self.out_dir_var = tk.StringVar(value=default_out)
        ttk.Entry(top_frame, textvariable=self.out_dir_var, width=50).pack(side='left', padx=5)
        ttk.Button(top_frame, text="Browse...", command=self.browse_output).pack(side='left')
        
        self.auto_open_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top_frame, text="Auto-open folder on complete", variable=self.auto_open_var).pack(side='left', padx=10)

        self.main_notebook = ttk.Notebook(root)
        self.main_notebook.pack(fill='both', expand=True, padx=10, pady=5)

        self.tab_susc = ttk.Frame(self.main_notebook)
        self.tab_se = ttk.Frame(self.main_notebook)

        self.main_notebook.add(self.tab_susc, text="Susceptibility")
        self.main_notebook.add(self.tab_se, text="Self-Energy")

        self.vars = {}
        self.running = False
        self.worker_thread = None

        self.build_susceptibility_ui(self.tab_susc)
        self.build_self_energy_ui(self.tab_se)

        # Bottom frame: Stop button + Status bar
        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill='x', side='bottom', padx=2, pady=2)
        
        self.btn_stop = ttk.Button(bottom_frame, text="⛔ Stop Execution", command=self.stop_execution, state="disabled")
        self.btn_stop.pack(side='right', padx=5)
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(fill='x', side='left', expand=True)

    def browse_output(self):
        folder = filedialog.askdirectory(initialdir=self.out_dir_var.get())
        if folder:
            self.out_dir_var.set(folder)

    def add_entry(self, parent, name, label, default, width=30):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=width).pack(side='left')
        var = tk.StringVar(value=default)
        self.vars[name] = var
        ttk.Entry(frame, textvariable=var).pack(side='left', expand=True, fill='x')

    def add_check(self, parent, name, label, default):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        var = tk.BooleanVar(value=default)
        self.vars[name] = var
        ttk.Checkbutton(frame, text=label, variable=var).pack(side='left')

    def add_combo(self, parent, name, label, options, default, width=30):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=width).pack(side='left')
        var = tk.StringVar(value=default)
        self.vars[name] = var
        cb = ttk.Combobox(frame, textvariable=var, values=options, state='readonly')
        cb.pack(side='left', expand=True, fill='x')

    # =========================================================================
    # SUSCEPTIBILITY
    # =========================================================================
    def build_susceptibility_ui(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill='both', expand=True, padx=5, pady=5)

        tab_sweep = ttk.Frame(nb)
        tab_phase = ttk.Frame(nb)
        tab_phys = ttk.Frame(nb)
        tab_num = ttk.Frame(nb)

        nb.add(tab_sweep, text="Sweep")
        nb.add(tab_phase, text="Phase Diagram")
        nb.add(tab_phys, text="Physics Params")
        nb.add(tab_num, text="Numerical Params")

        # --- Sweep Config ---
        self.add_check(tab_sweep, "susc_run_static", "Run Static Sweep", True)
        self.add_check(tab_sweep, "susc_run_dynamic", "Run Dynamic Sweep", True)
        self.add_combo(tab_sweep, "susc_sweep_mode", "Sweep Mode", ["JK", "J"], "JK")
        self.add_entry(tab_sweep, "susc_sweep_values", "Sweep Values (comma separated)", "3.0, 6.0, 10.0")
        self.add_entry(tab_sweep, "susc_fixed_J", "Fixed J (if sweeping JK)", "6.0")
        self.add_entry(tab_sweep, "susc_fixed_JK", "Fixed JK (if sweeping J)", "6.0")
        self.add_combo(tab_sweep, "susc_solver_choice", "Solver", ["cpu", "gpu32", "gpu64"], "cpu")

        self.btn_susc_sweep = ttk.Button(tab_sweep, text="Generate Susceptibility Sweep!", command=self.run_susc_sweep_thread)
        self.btn_susc_sweep.pack(pady=10)

        # --- Phase Diagram ---
        self.add_entry(tab_phase, "susc_J_sweep_min", "J min", "0.0")
        self.add_entry(tab_phase, "susc_J_sweep_max", "J max", "10.0")
        self.add_entry(tab_phase, "susc_J_sweep_pts", "J pts", "20")
        self.add_entry(tab_phase, "susc_JK_sweep_min", "JK min", "0.0")
        self.add_entry(tab_phase, "susc_JK_sweep_max", "JK max", "10.0")
        self.add_entry(tab_phase, "susc_JK_sweep_pts", "JK pts", "20")
        self.add_combo(tab_phase, "susc_solver_phase", "Solver", ["cpu", "gpu32", "gpu64"], "cpu")
        
        self.btn_susc_phase = ttk.Button(tab_phase, text="Generate Phase Diagram!", command=self.run_susc_phase_thread)
        self.btn_susc_phase.pack(pady=10)

        # --- Physics Params ---
        self.add_entry(tab_phys, "susc_t", "Hopping (t)", "1.0")
        self.add_entry(tab_phys, "susc_t1", "Next-Hopping (t1)", "0.0")
        self.add_entry(tab_phys, "susc_mu", "Chemical Potential (mu)", "1.0")
        self.add_entry(tab_phys, "susc_K", "Intralayer Exchange (K)", "1.0")

        # --- Numerical Params ---
        self.add_entry(tab_num, "susc_N", "Master Grid Resolution (N)", "200")
        self.add_entry(tab_num, "susc_omega_max", "Omega Max", "10.0")
        self.add_entry(tab_num, "susc_num_omegas", "Num Omegas", "1200")
        self.add_entry(tab_num, "susc_eta", "Broadening (eta)", "0.005")

    def run_susc_sweep_thread(self):
        if self.running: return
        self.lock_ui()
        self.status_var.set("Running susceptibility sweep... Check console for detailed progress.")
        self.worker_thread = threading.Thread(target=self.execute_susc_sweep, daemon=True)
        self.worker_thread.start()

    def run_susc_phase_thread(self):
        if self.running: return
        self.lock_ui()
        self.status_var.set("Running phase diagram... Check console for detailed progress.")
        self.worker_thread = threading.Thread(target=self.execute_susc_phase, daemon=True)
        self.worker_thread.start()

    def execute_susc_sweep(self):
        try:
            with ModuleIsolator("susceptibility"):
                from parameters import ModelParameters
                import sweep_core
                
                from parameters import ModelParameters
                p = ModelParameters(
                    t = float(self.vars["susc_t"].get()),
                    t1 = float(self.vars["susc_t1"].get()),
                    mu = float(self.vars["susc_mu"].get()),
                    K = float(self.vars["susc_K"].get()),
                    N = int(self.vars["susc_N"].get()),
                    omega_max = float(self.vars["susc_omega_max"].get()),
                    num_omegas = int(self.vars["susc_num_omegas"].get()),
                    eta = float(self.vars["susc_eta"].get())
                )
                
                sweep_vals = [float(x.strip()) for x in self.vars["susc_sweep_values"].get().split(",")]
                mode = self.vars["susc_sweep_mode"].get()
                
                actual_out_dir = os.path.join(self.out_dir_var.get(), "susceptibility_results")
                
                sweep_core.run_sweep(
                    run_static=self.vars["susc_run_static"].get(),
                    run_dynamic=self.vars["susc_run_dynamic"].get(),
                    sweep_mode=mode,
                    sweep_values=sweep_vals,
                    fixed_J=float(self.vars["susc_fixed_J"].get()) if mode == "JK" else None,
                    fixed_JK=float(self.vars["susc_fixed_JK"].get()) if mode == "J" else None,
                    mu=float(self.vars["susc_mu"].get()),
                    solver_choice=self.vars["susc_solver_choice"].get(),
                    output_dir=actual_out_dir,
                    p=p
                )
                self.root.after(0, lambda: self.handle_success(actual_out_dir))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.handle_error(msg))

    def execute_susc_phase(self):
        try:
            with ModuleIsolator("susceptibility"):
                from parameters import ModelParameters
                import phase_diagram
                
                p = ModelParameters(
                    t = float(self.vars["susc_t"].get()),
                    t1 = float(self.vars["susc_t1"].get()),
                    mu = float(self.vars["susc_mu"].get()),
                    K = float(self.vars["susc_K"].get()),
                    N = int(self.vars["susc_N"].get()),
                    omega_max = float(self.vars["susc_omega_max"].get()),
                    num_omegas = int(self.vars["susc_num_omegas"].get()),
                    eta = float(self.vars["susc_eta"].get()),
                    solver = self.vars["susc_solver_phase"].get()
                )
                
                J_min = float(self.vars["susc_J_sweep_min"].get())
                J_max = float(self.vars["susc_J_sweep_max"].get())
                J_pts = int(self.vars["susc_J_sweep_pts"].get())
                JK_min = float(self.vars["susc_JK_sweep_min"].get())
                JK_max = float(self.vars["susc_JK_sweep_max"].get())
                JK_pts = int(self.vars["susc_JK_sweep_pts"].get())
                
                actual_out_dir = os.path.join(self.out_dir_var.get(), "susceptibility_results")
                phase_diagram.run_phase_diagram(p, actual_out_dir,
                                                J_range=(J_min, J_max), J_pts=J_pts,
                                                JK_range=(JK_min, JK_max), JK_pts=JK_pts)
                self.root.after(0, lambda: self.handle_success(actual_out_dir))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.handle_error(msg))

    # =========================================================================
    # SELF-ENERGY
    # =========================================================================
    def build_self_energy_ui(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill='both', expand=True, padx=5, pady=5)

        tab_sweep = ttk.Frame(nb)
        tab_phys = ttk.Frame(nb)
        tab_num = ttk.Frame(nb)

        nb.add(tab_sweep, text="Sweep")
        nb.add(tab_phys, text="Physics Params")
        nb.add(tab_num, text="Numerical Params")

        # --- Sweep Params ---
        self.add_combo(tab_sweep, "se_sweep_mode", "Sweep Mode", ["J_perp", "JK"], "JK")
        self.add_entry(tab_sweep, "se_sweep_values", "Sweep Values (comma separated)", "3.0, 6.0, 9.0")
        self.add_entry(tab_sweep, "se_fixed_J_perp", "Fixed J_perp (if sweeping JK)", "6.0")
        self.add_entry(tab_sweep, "se_fixed_JK", "Fixed JK (if sweeping J_perp)", "6.0")
        self.add_combo(tab_sweep, "se_solver_choice", "Solver", ["cpu", "gpu32", "gpu64"], "cpu")

        self.btn_se_sweep = ttk.Button(tab_sweep, text="Generate Self-Energy Sweep!", command=self.run_se_sweep_thread)
        self.btn_se_sweep.pack(pady=10)

        # --- Physics Params ---
        self.add_entry(tab_phys, "se_t", "Hopping (t)", "1.0")
        self.add_entry(tab_phys, "se_mu", "Chemical Potential (mu)", "0.0")
        self.add_entry(tab_phys, "se_K", "Intralayer Exchange (K)", "1.0")

        # --- Numerical Params ---
        self.add_entry(tab_num, "se_N", "Grid Size (N)", "100")
        self.add_entry(tab_num, "se_eta", "Lorentzian Broadening (eta)", "0.05")
        self.add_entry(tab_num, "se_omega_max", "Omega Max", "60.0")
        self.add_entry(tab_num, "se_num_omega", "Num Omega (odd)", "4801")

    def run_se_sweep_thread(self):
        if self.running: return
        self.lock_ui()
        self.status_var.set("Running self-energy sweep... Check console for detailed progress.")
        self.worker_thread = threading.Thread(target=self.execute_se_sweep, daemon=True)
        self.worker_thread.start()

    def execute_se_sweep(self):
        try:
            with ModuleIsolator("self_energy"):
                import sweep_core
                
                sweep_vals = [float(x.strip()) for x in self.vars["se_sweep_values"].get().split(",")]
                mode = self.vars["se_sweep_mode"].get()
                
                actual_out_dir = os.path.join(self.out_dir_var.get(), "spectral_results")
                
                from parameters import ModelParameters
                w_max = float(self.vars["se_omega_max"].get())
                p = ModelParameters(
                    t=float(self.vars["se_t"].get()),
                    mu=float(self.vars["se_mu"].get()),
                    K=float(self.vars["se_K"].get()),
                    N=int(self.vars["se_N"].get()),
                    eta=float(self.vars["se_eta"].get()),
                    omega_min=-w_max,
                    omega_max=w_max,
                    num_omega=int(self.vars["se_num_omega"].get()),
                    solver=self.vars["se_solver_choice"].get()
                )
                
                if mode == "J_perp":
                    sweep_core.run_J_perp_sweep(
                        j_perp_values=sweep_vals,
                        fixed_jk=float(self.vars["se_fixed_JK"].get()),
                        mu=float(self.vars["se_mu"].get()),
                        solver_choice=self.vars["se_solver_choice"].get(),
                        output_dir=actual_out_dir,
                        p=p
                    )
                elif mode == "JK":
                    sweep_core.run_J_k_sweep(
                        j_k_values=sweep_vals,
                        base_j_k=1.0,
                        fixed_jperp=float(self.vars["se_fixed_J_perp"].get()),
                        mu=float(self.vars["se_mu"].get()),
                        solver_choice=self.vars["se_solver_choice"].get(),
                        output_dir=actual_out_dir,
                        p=p
                    )
                
                self.root.after(0, lambda: self.handle_success(actual_out_dir))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.handle_error(msg))

    # =========================================================================
    # SHARED UI LOGIC
    # =========================================================================
    def lock_ui(self):
        self.btn_susc_sweep.config(state="disabled")
        self.btn_susc_phase.config(state="disabled")
        self.btn_se_sweep.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.running = True

    def unlock_ui(self):
        self.btn_susc_sweep.config(state="normal")
        self.btn_susc_phase.config(state="normal")
        self.btn_se_sweep.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.running = False
        self.worker_thread = None

    def stop_execution(self):
        if self.worker_thread and self.worker_thread.is_alive():
            tid = self.worker_thread.ident
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_ulong(tid), ctypes.py_object(SystemExit))
            self.status_var.set("Stopped by user.")
            print("\n[STOP] Execution stopped by user.")
            self.root.after(500, self.unlock_ui)
        
    def handle_error(self, msg):
        self.status_var.set("Error occurred.")
        messagebox.showerror("Error", msg)
        self.unlock_ui()

    def handle_success(self, actual_out_dir):
        self.status_var.set('Finished successfully!')
        if self.auto_open_var.get() and os.path.exists(actual_out_dir):
            if os.name == 'nt':
                os.startfile(actual_out_dir)
        messagebox.showinfo('Success', f'Plots generated in:\n{actual_out_dir}')
        self.unlock_ui()

if __name__ == '__main__':
    root = tk.Tk()
    app = MasterApp(root)
    root.geometry('650x550')
    root.mainloop()
