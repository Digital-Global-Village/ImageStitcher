#!/usr/bin/env python3
"""
image_stitcher_gui.py

Polished Tkinter GUI for Python ImageStitcher.
"""

from __future__ import annotations

import math
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from PIL import ImageTk

from stitch_images import (
    PreparedImage,
    StitchError,
    StitchOptions,
    load_source_images,
    output_size,
    prepare_images,
    resize_with_quality,
    save_image,
    stitch_prepared_images,
    validate_output_size,
    validate_paths,
)


IMAGE_FILETYPES = [
    ("Images", "*.jpg *.jpeg *.png *.webp *.heic *.heif *.tif *.tiff"),
    ("All files", "*.*"),
]
PREVIEW_MAX_EDGE = 1800
PREVIEW_MAX_PIXELS = 2_800_000


class ImageStitcherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ImageStitcher")
        self.geometry("1120x720")
        self.minsize(960, 600)

        self.source_paths: list[Path] = []
        self.source_items: list[PreparedImage] = []
        self.preview_output: Any | None = None
        self.preview_photo: ImageTk.PhotoImage | None = None
        self.last_full_size: tuple[int, int] | None = None

        self.direction = tk.StringVar(value="vertical")
        self.spacing = tk.StringVar(value="0")
        self.background = tk.StringVar(value="transparent")
        self.custom_background = tk.StringVar(value="#ffffff")
        self.output_format = tk.StringVar(value="png")
        self.quality = tk.IntVar(value=95)
        self.scale_mode = tk.StringVar(value="smart match (recommended)")
        self.custom_size = tk.StringVar(value="")
        self.no_upscale = tk.BooleanVar(value=True)
        self.alignment = tk.StringVar(value="center")
        self.enhance = tk.StringVar(value="none")
        self.preset = tk.StringVar(value="Custom")
        self.estimate = tk.StringVar(value="Add images to begin.")
        self.status = tk.StringVar(value="Ready")

        self.configure(background="#ececec")
        self.apply_mac_style()
        self.create_widgets()
        self.bind_shortcuts()

        dropped_or_opened = [Path(arg) for arg in sys.argv[1:] if Path(arg).exists()]
        if dropped_or_opened:
            self.add_paths(dropped_or_opened)

    def apply_mac_style(self) -> None:
        style = ttk.Style(self)
        if "aqua" in style.theme_names():
            style.theme_use("aqua")
        style.configure("Toolbar.TFrame", padding=(12, 10))
        style.configure("Sidebar.TFrame", padding=(12, 0, 10, 10))
        style.configure("Inspector.TLabelframe", padding=10)
        style.configure("Status.TLabel", foreground="#5f6368")
        style.configure("Title.TLabel", font=("TkDefaultFont", 18, "bold"))
        style.configure("Muted.TLabel", foreground="#6d6d6d")

    def bind_shortcuts(self) -> None:
        self.bind("<Command-o>", lambda _event: self.add_images())
        self.bind("<Command-s>", lambda _event: self.save_as())
        self.bind("<BackSpace>", lambda _event: self.remove_selected())
        self.bind("<Command-r>", lambda _event: self.refresh_preview())

    def create_widgets(self) -> None:
        toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        toolbar.pack(fill=tk.X)
        ttk.Label(toolbar, text="ImageStitcher", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Add Images", command=self.add_images).pack(side=tk.RIGHT)
        ttk.Button(toolbar, text="Save As", command=self.save_as).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(toolbar, text="Preview", command=self.refresh_preview).pack(side=tk.RIGHT, padx=(0, 8))

        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, style="Sidebar.TFrame")
        center = ttk.Frame(main, padding=(0, 0, 12, 10))
        right = ttk.Frame(main, padding=(0, 0, 12, 10))
        main.add(left, weight=2)
        main.add(center, weight=4)
        main.add(right, weight=2)

        self.create_image_table(left)
        self.create_preview(center)
        self.create_inspector(right)

        status_bar = ttk.Frame(self, padding=(12, 6))
        status_bar.pack(fill=tk.X)
        ttk.Label(status_bar, textvariable=self.status, style="Status.TLabel").pack(side=tk.LEFT)
        ttk.Label(status_bar, textvariable=self.estimate, style="Status.TLabel").pack(side=tk.RIGHT)

    def create_image_table(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text="Images", font=("TkDefaultFont", 14, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text="Order saved exactly as listed", style="Muted.TLabel").pack(side=tk.RIGHT)

        columns = ("name", "size")
        table = ttk.Frame(parent)
        table.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(table, columns=columns, show="headings", selectmode="browse", height=14)
        self.tree.heading("name", text="File")
        self.tree.heading("size", text="Size")
        self.tree.column("name", width=220, anchor=tk.W)
        self.tree.column("size", width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        actions = ttk.Frame(parent)
        actions.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(actions, text="Move Up", command=self.move_up).pack(side=tk.LEFT)
        ttk.Button(actions, text="Move Down", command=self.move_down).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Remove", command=self.remove_selected).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=(8, 0))

    def create_preview(self, parent: ttk.Frame) -> None:
        preview_header = ttk.Frame(parent)
        preview_header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(preview_header, text="Preview", font=("TkDefaultFont", 14, "bold")).pack(side=tk.LEFT)
        ttk.Label(preview_header, text="Downscaled for speed; export saves full quality", style="Muted.TLabel").pack(
            side=tk.RIGHT
        )

        self.preview_canvas = tk.Canvas(parent, background="#f7f7f7", highlightthickness=1, highlightbackground="#d6d6d6")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind("<Configure>", lambda _event: self.draw_preview())

    def create_inspector(self, parent: ttk.Frame) -> None:
        quick = ttk.LabelFrame(parent, text="Presets", style="Inspector.TLabelframe")
        quick.pack(fill=tk.X)
        preset_box = ttk.Combobox(
            quick,
            textvariable=self.preset,
            state="readonly",
            values=["Custom", "Receipts", "Tickets", "Screenshots", "PDF Pages"],
        )
        preset_box.pack(fill=tk.X)
        preset_box.bind("<<ComboboxSelected>>", lambda _event: self.apply_preset())

        settings = ttk.LabelFrame(parent, text="Layout", style="Inspector.TLabelframe")
        settings.pack(fill=tk.X, pady=(10, 0))
        self.row_radio(settings, "Direction", self.direction, [("Horizontal", "horizontal"), ("Vertical", "vertical")])
        self.row_entry(settings, "Spacing", self.spacing, "px")
        self.row_combo(
            settings,
            "Image Size",
            self.scale_mode,
            [
                "smart match (recommended)",
                "original sizes",
                "match heights",
                "match widths",
                "custom width",
                "custom height",
            ],
        )
        self.row_entry(settings, "Custom", self.custom_size, "px")
        self.row_combo(settings, "Alignment", self.alignment, ["start", "center", "end"])
        ttk.Checkbutton(settings, text="Do not upscale", variable=self.no_upscale, command=self.refresh_preview).pack(
            anchor=tk.W, pady=(6, 0)
        )

        export = ttk.LabelFrame(parent, text="Export", style="Inspector.TLabelframe")
        export.pack(fill=tk.X, pady=(10, 0))
        self.row_combo(export, "Format", self.output_format, ["png", "jpg", "tiff"])
        self.row_combo(export, "Background", self.background, ["transparent", "white", "black", "custom"])
        self.row_entry(export, "Custom BG", self.custom_background, "")

        quality_row = ttk.Frame(export)
        quality_row.pack(fill=tk.X, pady=5)
        ttk.Label(quality_row, text="JPG Quality", width=12).pack(side=tk.LEFT)
        ttk.Scale(quality_row, from_=1, to=100, variable=self.quality, command=lambda _v: self.update_estimate()).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Label(quality_row, textvariable=self.quality, width=4).pack(side=tk.LEFT, padx=(8, 0))

        enhance = ttk.LabelFrame(parent, text="Enhance", style="Inspector.TLabelframe")
        enhance.pack(fill=tk.X, pady=(10, 0))
        self.row_combo(enhance, "Mode", self.enhance, ["none", "autocontrast", "sharpen", "text"])
        ttk.Label(
            enhance,
            text="Use gently. PNG/TIFF are best for text-heavy images; JPG is better for photos.",
            style="Muted.TLabel",
            wraplength=250,
        ).pack(fill=tk.X, pady=(6, 0))

    def row_radio(self, parent: ttk.Frame, label: str, variable: tk.StringVar, values: list[tuple[str, str]]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text=label, width=12).pack(side=tk.LEFT)
        for title, value in values:
            ttk.Radiobutton(row, text=title, variable=variable, value=value, command=self.refresh_preview).pack(side=tk.LEFT)

    def row_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar, suffix: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text=label, width=12).pack(side=tk.LEFT)
        entry = ttk.Entry(row, textvariable=variable, width=12)
        entry.pack(side=tk.LEFT)
        entry.bind("<KeyRelease>", lambda _event: self.update_estimate())
        if suffix:
            ttk.Label(row, text=suffix).pack(side=tk.LEFT, padx=(6, 0))

    def row_combo(self, parent: ttk.Frame, label: str, variable: tk.StringVar, values: list[str]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=5)
        ttk.Label(row, text=label, width=12).pack(side=tk.LEFT)
        combo = ttk.Combobox(row, textvariable=variable, values=values, state="readonly")
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_preview())

    def add_images(self) -> None:
        filenames = filedialog.askopenfilenames(title="Choose Images", filetypes=IMAGE_FILETYPES)
        if filenames:
            self.add_paths([Path(name) for name in filenames])

    def add_paths(self, paths: list[Path]) -> None:
        try:
            valid = validate_paths([str(path) for path in paths])
            loaded = load_source_images(valid)
        except StitchError as exc:
            messagebox.showerror("ImageStitcher", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("ImageStitcher", f"Could not load images: {exc}")
            return

        self.source_paths.extend(valid)
        self.source_items.extend(loaded)
        self.populate_tree()
        self.status.set(f"Loaded {len(self.source_items)} image(s).")
        self.refresh_preview()

    def populate_tree(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for index, item in enumerate(self.source_items):
            width, height = item.original_size
            self.tree.insert("", tk.END, iid=str(index), values=(item.path.name, f"{width} x {height}"))

    def selected_index(self) -> int | None:
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def remove_selected(self) -> None:
        index = self.selected_index()
        if index is None:
            return
        del self.source_paths[index]
        del self.source_items[index]
        self.populate_tree()
        self.refresh_preview()

    def clear_all(self) -> None:
        self.source_paths.clear()
        self.source_items.clear()
        self.preview_output = None
        self.preview_photo = None
        self.last_full_size = None
        self.populate_tree()
        self.estimate.set("Add images to begin.")
        self.status.set("Cleared.")
        self.draw_preview()

    def move_up(self) -> None:
        index = self.selected_index()
        if index is None or index == 0:
            return
        self.swap_items(index, index - 1)

    def move_down(self) -> None:
        index = self.selected_index()
        if index is None or index >= len(self.source_items) - 1:
            return
        self.swap_items(index, index + 1)

    def swap_items(self, index: int, target: int) -> None:
        self.source_paths[index], self.source_paths[target] = self.source_paths[target], self.source_paths[index]
        self.source_items[index], self.source_items[target] = self.source_items[target], self.source_items[index]
        self.populate_tree()
        self.tree.selection_set(str(target))
        self.refresh_preview()

    def apply_preset(self) -> None:
        preset = self.preset.get()
        if preset == "Receipts":
            self.direction.set("vertical")
            self.scale_mode.set("smart match (recommended)")
            self.background.set("white")
            self.output_format.set("png")
            self.enhance.set("text")
            self.no_upscale.set(True)
        elif preset == "Tickets":
            self.direction.set("horizontal")
            self.scale_mode.set("smart match (recommended)")
            self.background.set("white")
            self.output_format.set("png")
            self.enhance.set("sharpen")
            self.no_upscale.set(True)
        elif preset == "Screenshots":
            self.direction.set("vertical")
            self.scale_mode.set("original sizes")
            self.background.set("transparent")
            self.output_format.set("png")
            self.enhance.set("none")
            self.no_upscale.set(True)
        elif preset == "PDF Pages":
            self.direction.set("vertical")
            self.scale_mode.set("smart match (recommended)")
            self.background.set("white")
            self.output_format.set("tiff")
            self.enhance.set("autocontrast")
            self.no_upscale.set(True)
        self.refresh_preview()

    def build_options(self) -> StitchOptions | None:
        try:
            spacing = int(self.spacing.get() or "0")
            custom = int(self.custom_size.get()) if self.custom_size.get().strip() else None
        except ValueError:
            self.status.set("Spacing and custom size must be whole numbers.")
            return None

        background = self.custom_background.get().strip() if self.background.get() == "custom" else self.background.get()
        mode = self.scale_mode.get()
        return StitchOptions(
            direction=self.direction.get(),
            spacing=spacing,
            background=background,
            output_format=self.output_format.get(),
            quality=self.quality.get(),
            smart_match=mode == "smart match (recommended)",
            same_height=mode == "match heights",
            same_width=mode == "match widths",
            max_width=custom if mode == "custom width" else None,
            max_height=custom if mode == "custom height" else None,
            no_upscale=self.no_upscale.get(),
            enhance=self.enhance.get(),
            alignment=self.alignment.get(),
        )

    def prepared_full(self) -> tuple[list[PreparedImage], StitchOptions, list[str]] | None:
        if not self.source_items:
            return None
        options = self.build_options()
        if options is None:
            return None
        try:
            prepared, warnings = prepare_images(self.source_items, options)
            return prepared, options, warnings
        except StitchError as exc:
            self.status.set(str(exc))
        except Exception as exc:
            self.status.set(f"Could not prepare images: {exc}")
        return None

    def update_estimate(self) -> None:
        full = self.prepared_full()
        if full is None:
            return
        prepared, options, warnings = full
        try:
            width, height = output_size(prepared, options)
            validate_output_size(width, height)
        except StitchError as exc:
            self.status.set(str(exc))
            return

        self.last_full_size = (width, height)
        warning_text = f" Warning: {warnings[0]}" if warnings else ""
        self.estimate.set(f"{len(prepared)} image(s) -> {width} x {height}px, {options.output_format.upper()}.{warning_text}")
        self.status.set("Settings updated.")

    def refresh_preview(self) -> None:
        full = self.prepared_full()
        if full is None:
            self.draw_preview()
            return

        prepared, options, warnings = full
        try:
            full_width, full_height = output_size(prepared, options)
            validate_output_size(full_width, full_height)
            preview_items, preview_options = self.make_preview_items(prepared, options, full_width, full_height)
            self.preview_output = stitch_prepared_images(preview_items, preview_options)
            self.last_full_size = (full_width, full_height)
            warning_text = f" Warning: {warnings[0]}" if warnings else ""
            self.estimate.set(
                f"{len(prepared)} image(s) -> {full_width} x {full_height}px, {options.output_format.upper()}.{warning_text}"
            )
            self.status.set("Preview ready.")
            self.draw_preview()
        except StitchError as exc:
            self.status.set(str(exc))
            messagebox.showerror("ImageStitcher", str(exc))
        except Exception as exc:
            self.status.set(f"Could not create preview: {exc}")
            messagebox.showerror("ImageStitcher", f"Could not create preview: {exc}")

    def make_preview_items(
        self,
        prepared: list[PreparedImage],
        options: StitchOptions,
        full_width: int,
        full_height: int,
    ) -> tuple[list[PreparedImage], StitchOptions]:
        edge_scale = min(1.0, PREVIEW_MAX_EDGE / max(full_width, full_height))
        pixel_scale = min(1.0, math.sqrt(PREVIEW_MAX_PIXELS / max(full_width * full_height, 1)))
        scale = min(edge_scale, pixel_scale)

        preview_items: list[PreparedImage] = []
        for item in prepared:
            new_size = (
                max(1, round(item.image.width * scale)),
                max(1, round(item.image.height * scale)),
            )
            preview_items.append(
                PreparedImage(
                    path=item.path,
                    image=resize_with_quality(item.image, new_size),
                    original_size=item.original_size,
                    scale=item.scale * scale,
                )
            )

        preview_options = StitchOptions(
            direction=options.direction,
            spacing=max(0, round(options.spacing * scale)),
            background=options.background,
            output_format=options.output_format,
            quality=options.quality,
            no_upscale=True,
            enhance="none",
            alignment=options.alignment,
        )
        return preview_items, preview_options

    def draw_preview(self) -> None:
        self.preview_canvas.delete("all")
        canvas_width = max(1, self.preview_canvas.winfo_width())
        canvas_height = max(1, self.preview_canvas.winfo_height())

        if self.preview_output is None:
            self.preview_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="Add images, choose settings, then click Preview.",
                fill="#686868",
                font=("TkDefaultFont", 14),
            )
            return

        image = self.preview_output.copy()
        image.thumbnail((max(1, canvas_width - 36), max(1, canvas_height - 36)))
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview_canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.preview_photo, anchor=tk.CENTER)

    def save_as(self) -> None:
        full = self.prepared_full()
        if full is None:
            messagebox.showerror("ImageStitcher", "Add images before saving.")
            return
        prepared, options, _warnings = full

        fmt = options.output_format
        extension = {"png": ".png", "jpg": ".jpg", "tiff": ".tiff"}[fmt]
        filename = filedialog.asksaveasfilename(
            title="Save Stitched Image",
            defaultextension=extension,
            filetypes=[(fmt.upper(), f"*{extension}"), ("All files", "*.*")],
            initialfile=f"stitched_output{extension}",
        )
        if not filename:
            return

        try:
            self.status.set("Rendering full-quality export...")
            self.update_idletasks()
            output = stitch_prepared_images(prepared, options)
            saved = save_image(output, filename, options)
            self.status.set(f"Saved {saved}")
            messagebox.showinfo("ImageStitcher", f"Saved image to:\n{saved}")
        except StitchError as exc:
            self.status.set(str(exc))
            messagebox.showerror("ImageStitcher", str(exc))
        except Exception as exc:
            self.status.set(f"Could not save image: {exc}")
            messagebox.showerror("ImageStitcher", f"Could not save image: {exc}")


def main() -> None:
    app = ImageStitcherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
