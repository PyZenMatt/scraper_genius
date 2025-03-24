import tkinter as tk
import pandas as pd
from tkinter import ttk, messagebox, scrolledtext, filedialog
import queue
import threading
import logging
from src.scraper import search_songs, fetch_lyrics
from concurrent.futures import ThreadPoolExecutor, as_completed
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

class LyricsScraperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Genius Lyrics Scraper")
        self.geometry("1000x700")
        self.create_widgets()  # Inizializza i widget
        self.log_queue = queue.Queue()
        self.setup_logging()
        self.scraping_thread = None
        self.stop_event = threading.Event()
        self.artist_songs = []
        self.after(100, self.update_progress_animation)  # Avvia l'animazione dopo l'inizializzazione

    def update_progress_animation(self):
        # Verifica che self.progress esista prima di accedervi
        if hasattr(self, 'progress') and self.progress['mode'] == 'indeterminate':
            self.progress.step(1)
            self.after(50, self.update_progress_animation)

    def create_widgets(self):
        # Frame principale
        main_frame = tk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Input Artista
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill='x', pady=10)

        tk.Label(input_frame, text="Nome artista:").pack(side=tk.LEFT)
        self.artist_entry = tk.Entry(input_frame, width=50)
        self.artist_entry.pack(side=tk.LEFT, padx=10)

        self.load_button = tk.Button(input_frame, 
                                  text="Carica canzoni",
                                  command=self.load_artist_songs)
        self.load_button.pack(side=tk.LEFT)

        # Lista Canzoni
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True)

        self.songs_listbox = tk.Listbox(list_frame, 
                                      width=80, 
                                      height=20,
                                      selectmode=tk.MULTIPLE)
        self.songs_listbox.pack(side=tk.LEFT, fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.songs_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.songs_listbox.yview)

        # Controlli
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill='x', pady=10)

        self.select_all_btn = tk.Button(control_frame,
                                      text="Seleziona tutto",
                                      command=self.select_all_songs)
        self.select_all_btn.pack(side=tk.LEFT, padx=5)

        self.deselect_btn = tk.Button(control_frame,
                                    text="Deseleziona tutto",
                                    command=self.deselect_all_songs)
        self.deselect_btn.pack(side=tk.LEFT, padx=5)

        self.download_btn = tk.Button(control_frame,
                                    text="Scarica selezionati",
                                    command=self.download_selected)
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # Progresso e Log
        self.progress = ttk.Progressbar(main_frame, 
                                      orient="horizontal", 
                                      length=500, 
                                      mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = tk.Label(main_frame, text="Pronto")
        self.status_label.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(main_frame, 
                                                width=120, 
                                                height=10, 
                                                state='disabled')
        self.log_area.pack(fill='both', expand=True)

        self.stop_btn = tk.Button(main_frame, 
                                text="Ferma operazione", 
                                command=self.stop_operation,
                                state='disabled')
        self.stop_btn.pack(pady=10)

    def setup_logging(self):
        handler = QueueHandler(self.log_queue)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
        self.after(100, self.poll_log_queue)

    def poll_log_queue(self):
        while True:
            try:
                record = self.log_queue.get_nowait()
            except queue.Empty:
                break
            msg = self.format_log_message(record)
            self.log_area.configure(state='normal')
            self.log_area.insert(tk.END, msg + '\n')
            self.log_area.configure(state='disabled')
            self.log_area.see(tk.END)
        self.after(100, self.poll_log_queue)

    def format_log_message(self, record):
        return self.log_queue.queue[0].getMessage() if not self.log_queue.empty() else ''

    def load_artist_songs(self):
        artist = self.artist_entry.get().strip()
        if not artist:
            messagebox.showerror("Errore", "Inserire il nome dell'artista")
            return

        self.songs_listbox.delete(0, tk.END)
        self.status_label.config(text="Ricerca canzoni in corso...")
        self.load_button.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress.config(mode='indeterminate')
        self.progress.start()

        def update_gui(songs_chunk):
            self.songs_listbox.insert(tk.END, *songs_chunk)
            current_count = self.songs_listbox.size()
            self.status_label.config(text=f"Caricate {current_count} canzoni...")

        def fetch_task():
            try:
                self.artist_songs = search_songs(
                    artist, 
                    self.stop_event,
                    update_callback=lambda chunk: self.after(0, update_gui, chunk)
                )
                self.after(0, lambda: self.status_label.config(
                    text=f"Caricamento completato - {len(self.artist_songs)} canzoni"))
            except Exception as e:
                self.after(0, self.show_error, str(e))
            finally:
                self.after(0, lambda: self.load_button.config(state='normal'))
                self.after(0, lambda: self.stop_btn.config(state='disabled'))
                self.after(0, lambda: self.progress.stop())
                self.after(0, lambda: self.progress.config(mode='determinate'))
                self.after(0, lambda: self.progress.config(value=100))

        threading.Thread(target=fetch_task, daemon=True).start()

    def select_all_songs(self):
        self.songs_listbox.selection_set(0, tk.END)

    def deselect_all_songs(self):
        self.songs_listbox.selection_clear(0, tk.END)

    def download_selected(self):
        selected = self.songs_listbox.curselection()
        if not selected:
            messagebox.showwarning("Attenzione", "Selezionare almeno una canzone")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Tutti i file", "*.*")]
        )

        if file_path:
            self.stop_btn.config(state='normal')
            selected_songs = [self.artist_songs[i] for i in selected]
            total = len(selected_songs)

            def download_task():
                results = []
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = {executor.submit(fetch_lyrics, song): i 
                             for i, song in enumerate(selected_songs)}
                    
                    for future in as_completed(futures):
                        if self.stop_event.is_set():
                            break
                        try:
                            result = future.result()
                            results.append(result)
                            self.update_progress(futures[future] + 1, total)
                        except Exception as e:
                            logging.error(f"Errore: {e}")

                if not self.stop_event.is_set():
                    df = pd.DataFrame(results)
                    df.to_csv(file_path, index=False)
                    messagebox.showinfo("Successo", f"Salvati {len(results)} testi")
                self.after(0, self.reset_ui)

            threading.Thread(target=download_task, daemon=True).start()

    def update_progress(self, current, total):
        self.after(0, self._update_progress, current, total)

    def _update_progress(self, current, total):
        progress = (current / total) * 100
        self.progress['value'] = progress
        self.status_label.config(text=f"Completato: {current}/{total} ({progress:.1f}%)")

    def stop_operation(self):
        self.stop_event.set()
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="Operazione interrotta")
        self.progress.stop()
        self.progress.config(mode='determinate')

    def reset_ui(self):
        self.stop_event.clear()
        self.stop_btn.config(state='disabled')
        self.progress['value'] = 0

    def show_error(self, message):
        messagebox.showerror("Errore", message)
        self.status_label.config(text="Errore")
        self.reset_ui()

if __name__ == "__main__":
    app = LyricsScraperApp()
    app.mainloop()