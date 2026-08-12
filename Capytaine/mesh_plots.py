#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 06:18:38 2026

@author: troy
"""

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def plot_mesh_profile(mesh, cg_z=None):
    """Plot an x-z projection of a Capytaine mesh, including mesh edges."""

    vertices = mesh.vertices
    faces = mesh.faces

    segments = []

    for face in faces:
        face = [i for i in face if i >= 0]

        indices = face + [face[0]]

        for i1, i2 in zip(indices[:-1], indices[1:]):
            x1, z1 = vertices[i1, 0], vertices[i1, 2]
            x2, z2 = vertices[i2, 0], vertices[i2, 2]

            segments.append([
                (x1, z1),
                (x2, z2),
            ])

    fig, ax = plt.subplots(figsize=(6, 8))

    mesh_lines = LineCollection(
        segments,
        linewidths=0.5,
    )

    ax.add_collection(mesh_lines)

    # Still-water level
    ax.axhline(
        0.0,
        linestyle="--",
        label="Still-water level",
    )

    # Center of gravity
    if cg_z is not None:
        ax.plot(
            0.0,
            cg_z,
            marker="x",
            markersize=10,
            markeredgewidth=2,
            linestyle="None",
            label="Center of gravity",
        )

    ax.autoscale()
    #ax.set_aspect("equal")

    ax.set_xlabel("x [m]")
    ax.set_ylabel("z [m]")
    ax.grid()

    if cg_z is not None:
        ax.legend()

    plt.tight_layout()
    plt.show()

    return fig, ax