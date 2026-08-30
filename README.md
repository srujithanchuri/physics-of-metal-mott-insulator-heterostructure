# Magnetic Instabilities in 2D Metal - Mott Insulator Heterostructures

## Overview
This repository provides the computational tools to investigate the magnetic instability of a 2D paramagnetic metal
under the influence of strong interactions. Specifically, it models a heterostructure consisting of a non-interacting 
fermion layer and a bilayer paramagnetic Mott insulator, coupled via the Kondo interaction. 

This repo contains numerical solvers, using which one can simulate how increasing the Kondo interaction—or driving the
Mott insulator towards a magnetic quantum critical point—triggers a magnetic instability in the metallic layer.
By computing static and dynamic observables, the generated phase diagrams and spectral data allow us to track this 
instability and understand it as a condensation of paramagnons at the appropriate wavevector. 

The heterostructure considered here is known as the **ancilla model**, which has recently been studied in the context of cuprates.
In the appropriate limit, this model maps to the single-band Hubbard model, making these numerical solvers highly relevant for 
exploring metallic magnetic phase transitions within Hubbard systems.

## The Physical Model
The system consists of a metallic layer ($c$) and two layers of a Mott insulator ($S_1$ and $S_2$).

![Model](attachments/Screenshot%202026-08-30%20055001.png)

The full Hamiltonian of the system is given by:

$$
\begin{aligned}
    H =&-\sum_i t_{ij}c^\dagger_{i\alpha}c_{j\alpha} 
    - \mu\sum_i c^\dagger_{i\alpha}c_{i\alpha} 
    +J_K\sum_i\mathbf{S}_{i1}\cdot c^\dagger_{i\alpha}\frac{\mathbf{\sigma}_{\alpha\beta}}{2}c_{i\beta} \\
    &\hspace{2.5em}+ \,J_\perp\sum_i \mathbf{S}_{i1}\cdot \mathbf{S}_{i2} ~+ \sum_{ij,m} K_{ij}^{mm}\mathbf{S}_{im} \cdot \mathbf{S}_{jm}
\end{aligned}
$$

Where:
* $t_{ij}$ is the hopping parameter for the metallic layer.
* $\mu$ is the chemical potential.
* $J_K$ is the Kondo coupling between the metallic layer and the first layer of the Mott insulator.
* $J_\perp$ is the interlayer antiferromagnetic coupling between the spin layers $S_1$ and $S_2$.
* $K_{ij}^{mm}$ is the intralayer antiferromagnetic exchange coupling within the spin layers.

### Spin Subsystem (Mott Insulator)
Isolating just the Mott insulator portion of the Hamiltonian, we can represent the spins using triplon operators 
( $t_{\mathbf{k}\alpha}$ ) and perform a Bogoliubov transformation to diagonalize the spin Hamiltonian. The resulting Hamiltonian in momentum space is:

![Spin_Model](attachments/Screenshot%202026-08-30%20055025.png)

$$
\begin{aligned}
    H_M = \sum_{\mathbf{k},\alpha} \left[ A_{\mathbf{k}} t_{\mathbf{k}\alpha}^\dagger t_{\mathbf{k}\alpha}  + \frac{B_{\mathbf{k}}}{2}(t_{\mathbf{k}\alpha}^\dagger t_{-\mathbf{k}\alpha}^\dagger + \text{H.c.}) \right]
\end{aligned}
$$

To study electronic properties, we calculate the retarded self-energy corrections ($\Sigma^R$) to the metallic Green's function 
($G^R$) upto second order in the Kondo coupling.  This allows us to calculate the spectral properties of the metallic layer. 
We then use Random Phase approximation(RPA) to calculate the interacting susceptibility ($\chi$). The onset of a magnetic 
instability is mathematically signaled by a divergence in this RPA susceptibility at a specific ordering wavevector.
The self energy and susceptibility calculations are riddled with poles and singularities which require careful numerical treatment. 
We take different approches to handle these singularities in the self energy and susceptibility calculations.


## Project Structure & Solvers

Because selfenergy and susceptibility calculations use wildly different numerical techniques to handle their respective singularities, they are implemented as independent solvers in their own submodules.
* **[Self-Energy Solver](self_energy_solver/)**: Calculates self-energy corrections ($\Sigma^R$) using Fast Fourier Transforms (FFTs) to evaluate complex $\mathcal{O}(N^6)$ momentum convolutions efficiently in real space (CuPy/GPU accelerated).
* **[RPA Susceptibility Solver](susceptibility/)**: Computes susceptibility ($\chi_0$) using the geometrical Linear Tetrahedron Method (LTM) to avoid artificial broadening, and constructs the fully renormalized interacting susceptibility via the Random Phase Approximation (RPA).
* **`conductivity_solver/`** *(In Development)*: A new solver being built from scratch to compute the optical/DC conductivity of the system.
* **`results/`**: A top-level directory intended for aggregated, multi-panel plots that tie the data from all independent solvers together into a unified physical picture.

## Cloning this Repository
Because this project utilizes Git Submodules to link to the independent solvers, a standard `git clone` will leave the solver directories empty. 

To clone this master repository and automatically pull down all the solver code, run:
```bash
git clone --recurse-submodules https://github.com/srujithanchuri/main_thesis.git
```
*(If you already cloned it normally and the folders are empty, you can populate them by running `git submodule update --init --recursive`)*.
