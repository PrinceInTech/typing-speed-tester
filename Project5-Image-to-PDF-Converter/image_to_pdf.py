"""
Image to PDF Converter
=======================
Features:
  - Multiple image upload (JPG, PNG, BMP, WEBP, GIF, TIFF)
  - Thumbnail preview grid
  - Move Up / Move Down reordering
  - Remove selected / Clear all
  - Output filename customization
  - Page size selection (A4, Letter, A3, Original)
  - PDF generation using Pillow
  - Progress bar during conversion
  - Dark theme GUI
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
from datetime import datetime

# ── Theme ──────────────────────────────────────────────────────
T = {
    "bg":      "#0F1117",
    "surface": "#1A1D27",
    "card":    "#22263A",
    "border":  "#2E3350",
    "accent":  "#7C6FF7",
    "accent2": "#4ECDC4",
    "text":    "#E8EAF6",
    "subtext": "#8B90B8",
    "success": "#43A047",
    "error":   "#FF6B6B",
}

PAGE_SIZES = {
    "A4 (210x297 mm)":    (595, 842),
    "Letter (8.5x11 in)": (612, 792),
    "A3 (297x420 mm)":    (842, 1191),
    "Original Size":       None,
}

SUPPORTED = [
    ("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.tif *.webp"),
    ("All Files", "*.*"),
]

THUMB_W, THUMB_H = 110, 90


# ── Data class ──────────────────────────────────────────────────
class ImageEntry:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self._thumb = None

    def get_thumb(self):
        if self._thumb is None:
            img = Image.open(self.path)
            img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
            canvas = Image.new("RGB", (THUMB_W, THUMB_H), (34, 38, 58))
            off = ((THUMB_W - img.width)//2, (THUMB_H - img.height)//2)
            canvas.paste(img, off)
            self._thumb = ImageTk.PhotoImage(canvas)
        return self._thumb


# ── Conversion logic ────────────────────────────────────────────
def convert_to_pdf(entries, output_path, page_size_name, progress_cb=None):
    if not entries:
        raise ValueError("No images selected!")

    page_size = PAGE_SIZES[page_size_name]
    images_pil = []

    for i, entry in enumerate(entries):
        if progress_cb:
            progress_cb(i / len(entries), f"Processing {entry.name}...")

        img = Image.open(entry.path).convert("RGB")

        if page_size is not None:
            pw, ph = page_size
            iw, ih = img.size
            scale = min(pw / iw, ph / ih)
            nw, nh = int(iw * scale), int(ih * scale)
            img = img.resize((nw, nh), Image.LANCZOS)
            page = Image.new("RGB", (pw, ph), (255, 255, 255))
            page.paste(img, ((pw - nw)//2, (ph - nh)//2))
            img = page

        images_pil.append(img)

    if progress_cb:
        progress_cb(0.9, "Generating PDF...")

    first = images_pil[0]
    rest  = images_pil[1:]
    first.save(output_path, save_all=True, append_images=rest)

    if progress_cb:
        progress_cb(1.0, "Done!")

    return output_path


# ── GUI ─────────────────────────────────────────────────────────
class ImgToPDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to PDF Converter")
        self.root.configure(bg=T["bg"])
        self.root.resizable(True, True)
        self.root.minsize(820, 600)

        self.entries = []
        self._sel = -1
        self._build_ui()

    def _build_ui(self):
        # Top bar
        bar = tk.Frame(self.root, bg=T["surface"], pady=10)
        bar.pack(fill="x")
        tk.Label(bar, text="🖼️  Image to PDF Converter",
                 font=("Helvetica", 17, "bold"),
                 fg=T["accent"], bg=T["surface"]).pack(side="left", padx=20)
        tk.Label(bar, text="JPG · PNG · BMP · WEBP → PDF",
                 font=("Helvetica", 10),
                 fg=T["subtext"], bg=T["surface"]).pack(side="right", padx=20)

        main = tk.Frame(self.root, bg=T["bg"])
        main.pack(fill="both", expand=True, padx=14, pady=10)

        # ── Left panel ──
        left = tk.Frame(main, bg=T["bg"], width=200)
        left.pack(side="left", fill="y", padx=(0,10))
        left.pack_propagate(False)

        tk.Label(left, text="IMAGE LIST", font=("Helvetica", 9, "bold"),
                 fg=T["border"], bg=T["bg"]).pack(anchor="w", pady=(0,4))

        lb_f = tk.Frame(left, bg=T["border"])
        lb_f.pack(fill="both", expand=True)
        self._lb = tk.Listbox(lb_f, bg=T["surface"], fg=T["text"],
                              selectbackground=T["accent"],
                              selectforeground="white",
                              font=("Helvetica", 10),
                              relief="flat", bd=0, activestyle="none")
        self._lb.pack(side="left", fill="both", expand=True)
        self._lb.bind("<<ListboxSelect>>", self._on_sel)

        sb = tk.Scrollbar(lb_f, command=self._lb.yview,
                          bg=T["surface"], troughcolor=T["border"])
        sb.pack(side="right", fill="y")
        self._lb.config(yscrollcommand=sb.set)

        # Order buttons
        row = tk.Frame(left, bg=T["bg"])
        row.pack(fill="x", pady=6)
        self._fbtn(row, "⬆ Up",   self._move_up).pack(side="left", expand=True, fill="x", padx=2)
        self._fbtn(row, "⬇ Down", self._move_down).pack(side="left", expand=True, fill="x", padx=2)

        self._fbtn(left, "🗑 Remove", self._remove, T["error"]).pack(fill="x", pady=2)
        self._fbtn(left, "🗑 Clear All", self._clear, T["error"]).pack(fill="x", pady=2)

        self._cnt = tk.Label(left, text="0 images", font=("Helvetica",10),
                             fg=T["subtext"], bg=T["bg"])
        self._cnt.pack(pady=4)

        # ── Right panel ──
        right = tk.Frame(main, bg=T["bg"])
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="PREVIEW", font=("Helvetica",9,"bold"),
                 fg=T["border"], bg=T["bg"]).pack(anchor="w")

        pf = tk.Frame(right, bg=T["surface"], height=300)
        pf.pack(fill="both", expand=True, pady=(4,10))
        pf.pack_propagate(False)

        self._cv = tk.Canvas(pf, bg=T["surface"], highlightthickness=0)
        self._cv.pack(side="left", fill="both", expand=True)
        vsb = tk.Scrollbar(pf, orient="vertical", command=self._cv.yview)
        vsb.pack(side="right", fill="y")
        self._cv.configure(yscrollcommand=vsb.set)

        self._tf = tk.Frame(self._cv, bg=T["surface"])
        self._cw = self._cv.create_window((0,0), window=self._tf, anchor="nw")
        self._tf.bind("<Configure>", lambda e: self._cv.configure(
            scrollregion=self._cv.bbox("all")))
        self._cv.bind("<Configure>", self._on_cv_cfg)

        self._drop = tk.Label(pf,
                              text="📂\n\nClick 'Add Images' to get started\n\nJPG · PNG · BMP · WEBP · GIF · TIFF",
                              font=("Helvetica",12), fg=T["subtext"],
                              bg=T["surface"], justify="center")
        self._drop.place(relx=0.5, rely=0.5, anchor="center")

        # Settings
        sf = tk.Frame(right, bg=T["card"], pady=10, padx=14)
        sf.pack(fill="x", pady=(0,8))

        tk.Label(sf, text="Output Filename:", font=("Helvetica",10,"bold"),
                 fg=T["text"], bg=T["card"]).grid(row=0, column=0, sticky="w", padx=(0,8))
        self._fname = tk.StringVar(
            value=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        tk.Entry(sf, textvariable=self._fname, font=("Helvetica",10),
                 bg=T["surface"], fg=T["accent2"], relief="flat",
                 insertbackground=T["accent"], width=28).grid(row=0, column=1)
        tk.Label(sf, text=".pdf", font=("Helvetica",10),
                 fg=T["subtext"], bg=T["card"]).grid(row=0, column=2)

        tk.Label(sf, text="Page Size:", font=("Helvetica",10,"bold"),
                 fg=T["text"], bg=T["card"]).grid(row=1, column=0, sticky="w", pady=(8,0))
        self._psize = tk.StringVar(value="A4 (210x297 mm)")
        ttk.Combobox(sf, textvariable=self._psize,
                     values=list(PAGE_SIZES.keys()),
                     state="readonly", width=24,
                     font=("Helvetica",10)).grid(row=1, column=1, sticky="w", pady=(8,0))

        # Progress
        self._prog = tk.DoubleVar(value=0)
        ttk.Progressbar(right, variable=self._prog, maximum=1.0).pack(fill="x", pady=(0,4))
        self._status = tk.StringVar(value="Ready")
        tk.Label(right, textvariable=self._status, font=("Helvetica",10),
                 fg=T["subtext"], bg=T["bg"]).pack(anchor="w")

        # Buttons
        br = tk.Frame(right, bg=T["bg"])
        br.pack(pady=8)
        self._abtn(br, "📂  Add Images", self._add).pack(side="left", padx=6)
        self._abtn(br, "📄  Convert to PDF", self._convert,
                   T["accent2"], T["bg"]).pack(side="left", padx=6)

    def _fbtn(self, p, t, c, col=None):
        return tk.Button(p, text=t, command=c,
                         bg=col or T["card"], fg=T["text"],
                         relief="flat", padx=6, pady=5,
                         font=("Helvetica",10), cursor="hand2",
                         activebackground=T["border"])

    def _abtn(self, p, t, c, col=None, fg=None):
        return tk.Button(p, text=t, command=c,
                         bg=col or T["accent"],
                         fg=fg or "#FFFFFF",
                         relief="flat", padx=18, pady=9,
                         font=("Helvetica",12,"bold"), cursor="hand2")

    def _on_cv_cfg(self, event):
        self._cv.itemconfig(self._cw, width=event.width)
        self._refresh_thumbs()

    def _on_sel(self, event):
        sel = self._lb.curselection()
        if sel:
            self._sel = sel[0]
            self._refresh_thumbs()

    def _add(self):
        paths = filedialog.askopenfilenames(title="Select Images",
                                            filetypes=SUPPORTED)
        if not paths:
            return
        existing = [e.path for e in self.entries]
        for p in paths:
            if p not in existing:
                self.entries.append(ImageEntry(p))
        self._refresh()

    def _refresh(self):
        self._lb.delete(0, "end")
        for i, e in enumerate(self.entries):
            self._lb.insert("end", f"  {i+1}. {e.name}")
        if 0 <= self._sel < len(self.entries):
            self._lb.selection_set(self._sel)
        self._cnt.config(text=f"{len(self.entries)} image{'s' if len(self.entries)!=1 else ''}")
        self._refresh_thumbs()
        if self.entries:
            self._drop.place_forget()
        else:
            self._drop.place(relx=0.5, rely=0.5, anchor="center")

    def _refresh_thumbs(self):
        for w in self._tf.winfo_children():
            w.destroy()
        cols = max(4, self._cv.winfo_width() // (THUMB_W + 16))
        for i, entry in enumerate(self.entries):
            cell = tk.Frame(self._tf, bg=T["card"],
                            highlightthickness=2,
                            highlightbackground=T["accent"] if i==self._sel else T["border"])
            cell.grid(row=i//cols, column=i%cols, padx=5, pady=5)
            try:
                th = entry.get_thumb()
                lbl = tk.Label(cell, image=th, bg=T["card"], cursor="hand2")
                lbl.image = th
                lbl.pack()
                lbl.bind("<Button-1>", lambda e, idx=i: self._click_thumb(idx))
            except Exception:
                tk.Label(cell, text="⚠", bg=T["card"], fg=T["error"]).pack()
            short = entry.name[:14] + ("…" if len(entry.name)>14 else "")
            tk.Label(cell, text=f"{i+1}. {short}",
                     font=("Helvetica",8), fg=T["subtext"],
                     bg=T["card"], wraplength=THUMB_W).pack()
            cell.bind("<Button-1>", lambda e, idx=i: self._click_thumb(idx))

    def _click_thumb(self, idx):
        self._sel = idx
        self._lb.selection_clear(0, "end")
        self._lb.selection_set(idx)
        self._refresh_thumbs()

    def _move_up(self):
        i = self._sel
        if i <= 0 or i >= len(self.entries): return
        self.entries[i], self.entries[i-1] = self.entries[i-1], self.entries[i]
        self._sel = i - 1
        self._refresh()

    def _move_down(self):
        i = self._sel
        if i < 0 or i >= len(self.entries)-1: return
        self.entries[i], self.entries[i+1] = self.entries[i+1], self.entries[i]
        self._sel = i + 1
        self._refresh()

    def _remove(self):
        i = self._sel
        if i < 0 or i >= len(self.entries):
            messagebox.showinfo("Remove", "Select an image first!")
            return
        self.entries.pop(i)
        self._sel = min(i, len(self.entries)-1)
        self._refresh()

    def _clear(self):
        if not self.entries: return
        if messagebox.askyesno("Clear All", "Remove all images?"):
            self.entries.clear()
            self._sel = -1
            self._refresh()

    def _convert(self):
        if not self.entries:
            messagebox.showwarning("No Images", "Please add at least one image!")
            return
        fname = self._fname.get().strip()
        if not fname:
            messagebox.showwarning("Filename", "Please enter an output filename!")
            return
        save_path = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            initialfile=fname + ".pdf",
            filetypes=[("PDF Files","*.pdf"),("All Files","*.*")])
        if not save_path: return

        self._prog.set(0)
        self._status.set("Converting...")
        self.root.update()

        try:
            def cb(ratio, msg):
                self._prog.set(ratio)
                self._status.set(msg)
                self.root.update()

            out = convert_to_pdf(self.entries, save_path, self._psize.get(), cb)
            self._status.set(f"Saved: {os.path.basename(out)}")
            messagebox.showinfo("Success!",
                f"PDF created!\n\nPages: {len(self.entries)}\nSaved to:\n{out}")
        except Exception as ex:
            self._prog.set(0)
            self._status.set(f"Error: {ex}")
            messagebox.showerror("Error", str(ex))


# ── Entry ───────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 900, 640
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    ImgToPDFApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
