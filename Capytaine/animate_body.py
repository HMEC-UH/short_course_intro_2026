#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 08:37:55 2026

@author: troy
"""
from numpy import pi

import capytaine as cpt
from capytaine.bem.airy_waves import airy_waves_free_surface_elevation
from capytaine.ui.vtk.animation import Animation

def animate_body(solver,full_body,body):
    
    diffraction_problem = cpt.DiffractionProblem(body=body, wave_direction=0.0, omega=2.0)
    diffraction_result = solver.solve(diffraction_problem)
    
    radiation_problem = cpt.RadiationProblem(body=body, radiating_dof="Heave", omega=2.0)
    radiation_result = solver.solve(radiation_problem)
    
    # Define a mesh of the free surface and compute the free surface elevation
    free_surface = cpt.FreeSurface(x_range=(-50, 50), y_range=(-50, 50), nx=150, ny=150)
    diffraction_elevation_at_faces = solver.compute_free_surface_elevation(free_surface, diffraction_result)
    radiation_elevation_at_faces = solver.compute_free_surface_elevation(free_surface, radiation_result)
    
    # Add incoming waves
    diffraction_elevation_at_faces = diffraction_elevation_at_faces + airy_waves_free_surface_elevation(free_surface, diffraction_problem)
    
    # Run the animations
    animation = Animation(loop_duration=diffraction_result.period)
    animation.add_body(full_body, faces_motion=None)
    animation.add_free_surface(free_surface, faces_elevation=0.5*diffraction_elevation_at_faces)
    animation.run(camera_position=(-30, -30, 30))  # The camera is oriented towards (0, 0, 0) by default.
    # animation.save("path/to/the/video/file.ogv", camera_position=(-30, -30, 30))
    
    animation = Animation(loop_duration=radiation_result.period)
    animation.add_body(full_body, faces_motion=full_body.dofs["Heave"])
    animation.add_free_surface(free_surface, faces_elevation=3.0*radiation_elevation_at_faces)
    animation.run(camera_position=(-30, -30, 30))
    
    
    
def setup_animation(solver, body, fs, omega, wave_amplitude, wave_direction):
    # SOLVE BEM PROBLEMS
    radiation_problems = [cpt.RadiationProblem(omega=omega, body=body.immersed_part(), radiating_dof=dof) for dof in body.dofs]
    radiation_results = solver.solve_all(radiation_problems)
    diffraction_problem = cpt.DiffractionProblem(omega=omega, body=body.immersed_part(), wave_direction=wave_direction)
    diffraction_result = solver.solve(diffraction_problem)

    dataset = cpt.assemble_dataset(radiation_results + [diffraction_result])
    rao = cpt.post_pro.rao(dataset, wave_direction=wave_direction)

    # COMPUTE FREE SURFACE ELEVATION
    # Compute the diffracted wave pattern
    incoming_waves_elevation = airy_waves_free_surface_elevation(fs, diffraction_result)
    diffraction_elevation = solver.compute_free_surface_elevation(fs, diffraction_result)

    # Compute the wave pattern radiated by the RAO
    radiation_elevations_per_dof = {res.radiating_dof: solver.compute_free_surface_elevation(fs, res) for res in radiation_results}
    radiation_elevation = sum(rao.sel(omega=omega, radiating_dof=dof).data * radiation_elevations_per_dof[dof] for dof in body.dofs)

    # SET UP ANIMATION
    # Compute the motion of each face of the mesh for the animation
    rao_faces_motion = sum(rao.sel(omega=omega, radiating_dof=dof).data * body.dofs[dof] for dof in body.dofs)

    # Set up scene
    animation = Animation(loop_duration=2*pi/omega)
    animation.add_body(body, faces_motion=wave_amplitude*rao_faces_motion)
    animation.add_free_surface(fs, wave_amplitude * (incoming_waves_elevation + diffraction_elevation + radiation_elevation))
    return animation

def rao_animation(solver,full_body):
    fs = cpt.FreeSurface(x_range=(-5, 5), y_range=(-5, 5), nx=100, ny=100)

    anim = setup_animation(solver, full_body, fs, omega=1.5, wave_amplitude=0.25, wave_direction=pi)
    anim.run(camera_position=(70, 70, 100), resolution=(800, 600))
    