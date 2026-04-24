"""Petit panneau local visible pour autoriser ou bloquer l'execution."""

from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path

from ghost_poker.control import (
    ControlPanelStatus,
    load_control_panel_state,
    set_control_panel_state,
)
from ghost_poker.utils import load_runtime_config


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Panneau local visible always-on-top pour Ghost-Poker."
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=None,
        help="Chemin du fichier d'etat JSON (defaut: valeur runtime).",
    )
    parser.add_argument(
        "--geometry",
        default="280x210+20+20",
        help="Geometrie Tk (defaut: 280x210+20+20).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    runtime_config = load_runtime_config()
    state_path = args.state_path or runtime_config.control_state_path
    set_control_panel_state(state_path, ControlPanelStatus.PAUSED, note="panel opened")

    root = tk.Tk()
    root.title("Ghost Poker Control")
    root.geometry(args.geometry)
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.configure(bg="#101418")

    header_var = tk.StringVar()
    detail_var = tk.StringVar()
    path_var = tk.StringVar(value=f"state: {state_path}")
    refresh_job: str | None = None

    def set_status(status: ControlPanelStatus, note: str) -> None:
        set_control_panel_state(state_path, status, note=note)
        refresh()

    def refresh() -> None:
        nonlocal refresh_job
        state = load_control_panel_state(state_path)
        header_var.set(f"Etat: {state.status.value}")
        detail_var.set(f"Maj: {state.updated_at or '-'}\nNote: {state.note or '-'}")
        refresh_job = root.after(250, refresh)

    def on_close() -> None:
        nonlocal refresh_job
        if refresh_job is not None:
            root.after_cancel(refresh_job)
        set_control_panel_state(state_path, ControlPanelStatus.PAUSED, note="panel closed")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    tk.Label(
        root,
        text="Ghost Poker",
        bg="#101418",
        fg="#f3f4f6",
        font=("Segoe UI", 14, "bold"),
    ).pack(pady=(12, 6))
    tk.Label(
        root,
        textvariable=header_var,
        bg="#101418",
        fg="#7dd3fc",
        font=("Segoe UI", 11, "bold"),
    ).pack()
    tk.Label(
        root,
        textvariable=detail_var,
        bg="#101418",
        fg="#d1d5db",
        justify="left",
        font=("Segoe UI", 9),
    ).pack(pady=(6, 10))
    tk.Label(
        root,
        textvariable=path_var,
        bg="#101418",
        fg="#9ca3af",
        font=("Segoe UI", 8),
        wraplength=250,
        justify="left",
    ).pack(pady=(0, 10))

    button_frame = tk.Frame(root, bg="#101418")
    button_frame.pack(fill="x", padx=12)

    buttons = [
        (
            "ARM NEXT",
            "#0f766e",
            lambda: set_status(ControlPanelStatus.ARMED_ONCE, "armed next action"),
        ),
        ("ARM HOLD", "#0369a1", lambda: set_status(ControlPanelStatus.ARMED, "armed persistent")),
        ("PAUSE", "#92400e", lambda: set_status(ControlPanelStatus.PAUSED, "paused by operator")),
        ("STOP", "#991b1b", lambda: set_status(ControlPanelStatus.STOPPED, "stopped by operator")),
    ]

    for index, (label, color, callback) in enumerate(buttons):
        tk.Button(
            button_frame,
            text=label,
            command=callback,
            bg=color,
            fg="#ffffff",
            activebackground=color,
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=index // 2, column=index % 2, padx=4, pady=4, sticky="ew")

    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    refresh()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
