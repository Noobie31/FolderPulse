# tab3.py
import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry  # pip install tkcalendar
import config
import scheduler  # new module for scheduling logic
import storage


class TabThree(ttk.Frame):
    """
    Tab 3: Configure "traffic signal" thresholds (in days) + Email & Auto Scheduler
      - Green: 0..G
      - Amber: G+1..A
      - Red:   A+1..R  (and beyond stays Red)
      - Email: Comma-separated recipient list
      - Auto Scheduler: Date, Time, Frequency
    """
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load_current()

    def _build_ui(self) -> None:
        # Main scrollable container
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        wrap = scrollable_frame
        current_row = 0

        # ========== SECTION 1: Thresholds ==========
        ttk.Label(wrap, text="File State Thresholds (in days)", font=("", 12, "bold")).grid(
            row=current_row, column=0, columnspan=3, sticky="w", pady=(16, 10), padx=16
        )
        current_row += 1

        # Green
        ttk.Label(wrap, text="Green alert").grid(row=current_row, column=0, sticky="w", pady=6, padx=16)
        self.green_var = tk.StringVar()
        ttk.Entry(wrap, textvariable=self.green_var, width=10).grid(row=current_row, column=1, sticky="w")
        current_row += 1

        # Amber
        ttk.Label(wrap, text="Amber alert").grid(row=current_row, column=0, sticky="w", pady=6, padx=16)
        self.amber_var = tk.StringVar()
        ttk.Entry(wrap, textvariable=self.amber_var, width=10).grid(row=current_row, column=1, sticky="w")
        current_row += 1

        # Red
        ttk.Label(wrap, text="Red alert").grid(row=current_row, column=0, sticky="w", pady=6, padx=16)
        self.red_var = tk.StringVar()
        ttk.Entry(wrap, textvariable=self.red_var, width=10).grid(row=current_row, column=1, sticky="w")
        current_row += 1

        # Helper text
        help_txt = (
            "Ranges:\n"
            "  Green: 0..G days\n"
            "  Amber: (G+1)..A days\n"
            "  Red:   (A+1)..R days (and beyond stays Red)"
        )
        ttk.Label(wrap, text=help_txt).grid(row=current_row, column=0, columnspan=3, sticky="w", pady=(8, 12), padx=16)
        current_row += 1

        # Save thresholds button
        ttk.Button(wrap, text="Save Thresholds", command=self._on_save_thresholds).grid(
            row=current_row, column=0, sticky="w", pady=6, padx=16
        )
        current_row += 1

        # Separator
        ttk.Separator(wrap, orient="horizontal").grid(row=current_row, column=0, columnspan=3, sticky="ew", pady=20, padx=16)
        current_row += 1

        # ========== SECTION 2: Email ==========
        ttk.Label(wrap, text="Email Configuration", font=("", 12, "bold")).grid(
            row=current_row, column=0, columnspan=3, sticky="w", pady=(0, 10), padx=16
        )
        current_row += 1

        ttk.Label(wrap, text="Recipients (comma-separated)").grid(row=current_row, column=0, sticky="w", pady=6, padx=16)
        current_row += 1

        email_frame = ttk.Frame(wrap)
        email_frame.grid(row=current_row, column=0, columnspan=3, sticky="ew", pady=(0, 12), padx=16)
        
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(email_frame, textvariable=self.email_var, width=50)
        email_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(email_frame, text="Send Now", command=self._on_send_now).pack(side="left", padx=(8, 0))
        current_row += 1

        # Separator
        ttk.Separator(wrap, orient="horizontal").grid(row=current_row, column=0, columnspan=3, sticky="ew", pady=20, padx=16)
        current_row += 1

        # ========== SECTION 3: Auto Scheduler ==========
        ttk.Label(wrap, text="Auto Scheduler", font=("", 12, "bold")).grid(
            row=current_row, column=0, columnspan=3, sticky="w", pady=(0, 10), padx=16
        )
        current_row += 1

        # Date picker
        ttk.Label(wrap, text="Start Date").grid(row=current_row, column=0, sticky="w", pady=6, padx=16)
        self.date_picker = DateEntry(wrap, width=20, background='darkblue', foreground='white', borderwidth=2)
        self.date_picker.grid(row=current_row, column=1, sticky="w", pady=6)
        current_row += 1

        # Time picker (using spinboxes for hours and minutes)
        ttk.Label(wrap, text="Start Time").grid(row=current_row, column=0, sticky="w", pady=6, padx=16)
        time_frame = ttk.Frame(wrap)
        time_frame.grid(row=current_row, column=1, sticky="w", pady=6)
        
        self.hour_var = tk.StringVar(value="09")
        self.minute_var = tk.StringVar(value="00")
        
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=self.hour_var, format="%02.0f")
        hour_spin.pack(side="left")
        ttk.Label(time_frame, text=":").pack(side="left", padx=2)
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=self.minute_var, format="%02.0f")
        minute_spin.pack(side="left")
        ttk.Label(time_frame, text="(24-hour format)").pack(side="left", padx=(8, 0))
        current_row += 1

        # Frequency dropdown
        ttk.Label(wrap, text="Frequency").grid(row=current_row, column=0, sticky="w", pady=6, padx=16)
        self.frequency_var = tk.StringVar()
        frequency_combo = ttk.Combobox(wrap, textvariable=self.frequency_var, width=20, state="readonly")
        frequency_combo['values'] = (
            "Hourly",
            "Daily", 
            "Every 2 days",
            "Every 3 days",
            "Weekly",
            "Fortnightly",
            "Monthly",
            "Every 6 months",
            "Yearly"
        )
        frequency_combo.current(1)  # Default to "Daily"
        frequency_combo.grid(row=current_row, column=1, sticky="w", pady=6)
        current_row += 1

        # Scheduler status
        self.scheduler_status_var = tk.StringVar(value="Status: Not scheduled")
        ttk.Label(wrap, textvariable=self.scheduler_status_var, foreground="gray").grid(
            row=current_row, column=0, columnspan=3, sticky="w", pady=(8, 6), padx=16
        )
        current_row += 1

        # Scheduler buttons
        btn_frame = ttk.Frame(wrap)
        btn_frame.grid(row=current_row, column=0, columnspan=3, sticky="w", pady=12, padx=16)
        
        ttk.Button(btn_frame, text="Start Scheduler", command=self._on_start_scheduler).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Stop Scheduler", command=self._on_stop_scheduler).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Send Test Email", command=self._on_test_email).pack(side="left")
        current_row += 1

        # Layout tweaks
        for i in range(3):
            wrap.columnconfigure(i, weight=0)
        wrap.columnconfigure(1, weight=1)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _load_current(self) -> None:
        # Load thresholds
        g, a, r = config.get_thresholds()
        self.green_var.set(str(g))
        self.amber_var.set(str(a))
        self.red_var.set(str(r))
        
        # Load email config
        emails = scheduler.get_email_recipients()
        self.email_var.set(", ".join(emails))
        
        # Update scheduler status
        self._update_scheduler_status()

    def _on_save_thresholds(self) -> None:
        try:
            g = int(self.green_var.get())
            a = int(self.amber_var.get())
            r = int(self.red_var.get())
            if g < 0 or a < 0 or r < 0:
                raise ValueError("Values must be non-negative.")
            if not (g <= a <= r):
                raise ValueError("Must satisfy: Green ≤ Amber ≤ Red.")
        except Exception as e:
            messagebox.showerror("Invalid thresholds", str(e))
            return

        config.set_thresholds(g, a, r)
        messagebox.showinfo("Saved", f"Thresholds updated:\nGreen={g}, Amber={a}, Red={r}")

    def _on_start_scheduler(self) -> None:
        # Save email recipients
        email_text = self.email_var.get().strip()
        if not email_text:
            messagebox.showerror("Error", "Please enter at least one email address.")
            return
        
        emails = [e.strip() for e in email_text.split(",") if e.strip()]
        if not emails:
            messagebox.showerror("Error", "Please enter valid email addresses.")
            return
        
        # Validate email format (basic)
        import re
        email_pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        invalid_emails = [e for e in emails if not email_pattern.match(e)]
        if invalid_emails:
            messagebox.showerror("Error", f"Invalid email format:\n{', '.join(invalid_emails)}")
            return
        
        scheduler.set_email_recipients(emails)
        
        # Get schedule settings
        start_date = self.date_picker.get_date()
        start_time = f"{self.hour_var.get()}:{self.minute_var.get()}"
        frequency = self.frequency_var.get()
        
        try:
            scheduler.start_scheduler(start_date, start_time, frequency)
            self._update_scheduler_status()
            messagebox.showinfo("Success", f"Scheduler started!\n\nFrequency: {frequency}\nRecipients: {len(emails)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start scheduler:\n{e}")

    def _on_stop_scheduler(self) -> None:
        scheduler.stop_scheduler()
        self._update_scheduler_status()
        messagebox.showinfo("Stopped", "Scheduler has been stopped.")

    def _on_test_email(self) -> None:
        email_text = self.email_var.get().strip()
        if not email_text:
            messagebox.showerror("Error", "Please enter at least one email address.")
            return
        
        emails = [e.strip() for e in email_text.split(",") if e.strip()]
        if not emails:
            messagebox.showerror("Error", "Please enter valid email addresses.")
            return
        
        try:
            scheduler.send_test_email(emails)
            messagebox.showinfo("Success", f"Test email sent to:\n{', '.join(emails)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send test email:\n{e}")

    def _on_send_now(self) -> None:
        """Send the latest report immediately to configured recipients."""
        email_text = self.email_var.get().strip()
        if not email_text:
            messagebox.showerror("Error", "Please enter at least one email address.")
            return
        
        emails = [e.strip() for e in email_text.split(",") if e.strip()]
        if not emails:
            messagebox.showerror("Error", "Please enter valid email addresses.")
            return
        
        # Validate email format (basic)
        import re
        email_pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        invalid_emails = [e for e in emails if not email_pattern.match(e)]
        if invalid_emails:
            messagebox.showerror("Error", f"Invalid email format:\n{', '.join(invalid_emails)}")
            return
        
        try:
            # Get latest report
            reports = storage.list_reports()
            if not reports:
                messagebox.showerror("Error", "No reports available to send.\n\nPlease generate a report first from the Analysis tab.")
                return
            
            latest_report = reports[0]  # Already sorted newest-first
            report_path = latest_report.get("path")
            report_title = latest_report.get("title", "Report")
            
            if not report_path or not os.path.exists(report_path):
                messagebox.showerror("Error", f"Report file not found:\n{report_path}")
                return
            
            # Send the report
            scheduler.send_report_email(emails, report_path, report_title)
            messagebox.showinfo("Success", f"Report sent successfully!\n\nRecipients: {', '.join(emails)}\nReport: {report_title}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send report:\n{e}")

    def _update_scheduler_status(self) -> None:
        if scheduler.is_scheduler_running():
            info = scheduler.get_scheduler_info()
            status_text = f"Status: Running | Next run: {info.get('next_run', 'Unknown')} | Frequency: {info.get('frequency', 'Unknown')}"
            self.scheduler_status_var.set(status_text)
        else:
            self.scheduler_status_var.set("Status: Not scheduled")