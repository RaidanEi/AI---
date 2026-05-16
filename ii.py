
import cv2
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading


class DominantColorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор доминирующего цвета изображения")
        self.root.geometry("1200x700")
        self.root.configure(bg='#2c3e50')

        # Переменные
        self.image_path = None
        self.original_image = None
        self.dominant_color = None
        self.all_colors = None

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg='#34495e', height=80)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Заголовок
        title_label = tk.Label(top_frame, text="Анализатор доминирующего цвета",
                               font=('Arial', 20, 'bold'),
                               bg='#34495e', fg='white')
        title_label.pack(pady=10)

        # Панель инструментов
        toolbar = tk.Frame(self.root, bg='#ecf0f1', height=50)
        toolbar.pack(fill=tk.X, padx=10)

        # Кнопки
        load_btn = tk.Button(toolbar, text="📁 Загрузить изображение",
                             command=self.load_image,
                             font=('Arial', 12), bg='#3498db', fg='white',
                             padx=20, pady=5, cursor='hand2')
        load_btn.pack(side=tk.LEFT, padx=10, pady=10)

        # Ползунок для количества цветов
        cluster_label = tk.Label(toolbar, text="Количество цветов для анализа:",
                                 font=('Arial', 10), bg='#ecf0f1')
        cluster_label.pack(side=tk.LEFT, padx=(20, 5))

        self.cluster_var = tk.IntVar(value=5)
        cluster_spinbox = tk.Spinbox(toolbar, from_=2, to=10, width=5,
                                     textvariable=self.cluster_var,
                                     font=('Arial', 10), state='readonly')
        cluster_spinbox.pack(side=tk.LEFT, padx=5)

        # Кнопка анализа
        analyze_btn = tk.Button(toolbar, text="🔍 Найти доминирующий цвет",
                                command=self.analyze_image,
                                font=('Arial', 12), bg='#27ae60', fg='white',
                                padx=20, pady=5, cursor='hand2', state='disabled')
        analyze_btn.pack(side=tk.LEFT, padx=20)
        self.analyze_btn = analyze_btn

        # Кнопка сохранения
        save_btn = tk.Button(toolbar, text="💾 Сохранить результат",
                             command=self.save_result,
                             font=('Arial', 12), bg='#f39c12', fg='white',
                             padx=20, pady=5, cursor='hand2', state='disabled')
        save_btn.pack(side=tk.LEFT, padx=10)
        self.save_btn = save_btn

        # Основная область для изображения и результатов
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Область изображения
        self.image_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.image_label = tk.Label(self.image_frame, bg='#34495e')
        self.image_label.pack(expand=True, padx=10, pady=10)

        # Область результатов
        self.result_frame = tk.Frame(main_frame, bg='#34495e', width=350)
        self.result_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.result_frame.pack_propagate(False)

        # Заголовок результатов
        result_title = tk.Label(self.result_frame, text="Результаты анализа",
                                font=('Arial', 16, 'bold'), bg='#34495e', fg='white')
        result_title.pack(pady=10)

        # Canvas для matplotlib
        self.figure = Figure(figsize=(4, 4), dpi=100, facecolor='#34495e')
        self.canvas = FigureCanvasTkAgg(self.figure, self.result_frame)
        self.canvas.get_tk_widget().pack(pady=10)

        # Информация о цвете
        self.color_info = tk.Label(self.result_frame, text="",
                                   font=('Arial', 11), bg='#34495e', fg='white',
                                   justify=tk.LEFT)
        self.color_info.pack(pady=10)

        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе. Загрузите изображение")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              bd=1, relief=tk.SUNKEN, anchor=tk.W,
                              bg='#ecf0f1', font=('Arial', 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_image(self):
        """Загрузка изображения через диалоговое окно"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")]
        )

        if file_path:
            self.image_path = file_path
            self.status_var.set(f"Загружено: {file_path.split('/')[-1]}")

            # Загрузка и отображение изображения
            self.original_image = cv2.imread(file_path)
            self.display_image()

            # Активация кнопок
            self.analyze_btn.config(state='normal')
            self.save_btn.config(state='disabled')

            # Очистка предыдущих результатов
            self.clear_results()

    def display_image(self):
        """Отображение загруженного изображения"""
        if self.original_image is not None:
            # Преобразование для отображения в tkinter
            img_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            # Масштабирование для отображения
            max_width = 700
            max_height = 500
            img_pil.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            img_tk = ImageTk.PhotoImage(img_pil)
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk

    def find_dominant_color(self, image, num_clusters=5):
        """Нахождение доминирующего цвета с помощью K-means"""
        # Изменение размера для ускорения обработки
        height, width = image.shape[:2]
        if height * width > 800 * 800:
            scale = min(800 / width, 800 / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))

        # Преобразование в 2D массив пикселей
        pixels = image.reshape(-1, 3)

        # Применение K-means
        pixels_float = np.float32(pixels)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(pixels_float, num_clusters, None,
                                        criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # Подсчет процентного соотношения
        centers = np.uint8(centers)
        label_counts = Counter(labels.flatten())
        total_pixels = len(labels)

        # Сортировка цветов по частоте
        colors_info = []
        for i in range(num_clusters):
            percentage = (label_counts[i] / total_pixels) * 100
            color_bgr = centers[i]
            color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
            colors_info.append({
                'color': color_rgb,
                'percentage': percentage,
                'bgr': color_bgr
            })

        # Сортировка по убыванию процента
        colors_info.sort(key=lambda x: x['percentage'], reverse=True)
        dominant = colors_info[0]['color']

        return dominant, colors_info

    def analyze_image(self):
        """Анализ изображения для нахождения доминирующего цвета"""
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
            return

        # Запуск анализа в отдельном потоке
        self.status_var.set("Анализ изображения... Пожалуйста, подождите")
        self.analyze_btn.config(state='disabled')

        thread = threading.Thread(target=self._analyze_thread)
        thread.start()

    def _analyze_thread(self):
        """Поток для анализа изображения"""
        try:
            num_clusters = self.cluster_var.get()
            dominant, colors = self.find_dominant_color(self.original_image, num_clusters)
            self.dominant_color = dominant
            self.all_colors = colors

            # Обновление интерфейса в основном потоке
            self.root.after(0, self.update_results, dominant, colors)
            self.root.after(0, lambda: self.status_var.set("Анализ завершен!"))
            self.root.after(0, lambda: self.save_btn.config(state='normal'))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при анализе: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Ошибка при анализе"))
        finally:
            self.root.after(0, lambda: self.analyze_btn.config(state='normal'))

    def update_results(self, dominant_color, colors):
        """Обновление результатов на экране"""
        # Очистка предыдущих графиков
        self.figure.clear()

        # Создание графика с палитрой цветов
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)

        # Отображение доминирующего цвета
        color_patch = np.zeros((50, 50, 3), dtype=np.uint8)
        color_patch[:] = dominant_color
        ax1.imshow(color_patch)
        ax1.set_title(f'Доминирующий цвет\nRGB{dominant_color}', fontsize=10, color='white')
        ax1.axis('off')

        # Отображение всех цветов с процентами
        colors_array = []
        percentages = []
        labels_text = []

        for color_info in colors[:8]:  # Показываем топ-8 цветов
            colors_array.append([c / 255 for c in color_info['color']])  # Нормализация для matplotlib
            percentages.append(color_info['percentage'])
            labels_text.append(f'{color_info["percentage"]:.1f}%')

        if colors_array:
            # Создание палитры
            color_grid = np.array([colors_array])
            ax2.imshow(color_grid, aspect='auto')
            ax2.set_xticks(range(len(colors_array)))
            ax2.set_xticklabels(labels_text, rotation=45, ha='right', fontsize=8, color='white')
            ax2.set_title('Все найденные цвета', fontsize=10, color='white')
            ax2.set_yticks([])

        # Настройка внешнего вида
        self.figure.patch.set_facecolor('#34495e')
        for ax in [ax1, ax2]:
            ax.set_facecolor('#34495e')
            for spine in ax.spines.values():
                spine.set_color('white')

        self.canvas.draw()

        # Обновление текстовой информации
        info_text = f"""
        📊 Детальная информация:

        🎨 Доминирующий цвет:
           RGB{dominant_color}

        📈 Распределение цветов:
        """

        for i, color_info in enumerate(colors[:5], 1):
            rgb = color_info['color']
            info_text += f"\n   {i}. RGB{rgb}: {color_info['percentage']:.1f}%"

        self.color_info.config(text=info_text)

    def save_result(self):
        """Сохранение результата в файл"""
        if self.dominant_color is None:
            return

        # Создание результирующего изображения
        if self.original_image is not None:
            height, width = self.original_image.shape[:2]
            result_height = height
            result_width = width + 250  # Добавляем место для палитры

            result_img = np.ones((result_height, result_width, 3), dtype=np.uint8) * 255

            # Копируем оригинальное изображение
            if len(self.original_image.shape) == 3:
                result_img[:height, :width] = self.original_image
            else:
                result_img[:height, :width] = cv2.cvtColor(self.original_image, cv2.COLOR_GRAY2BGR)

            # Добавляем палитру цветов
            palette_height = height // len(self.all_colors)
            for i, color_info in enumerate(self.all_colors):
                y_start = i * palette_height
                y_end = (i + 1) * palette_height if i < len(self.all_colors) - 1 else height
                color_bgr = color_info['bgr']
                result_img[y_start:y_end, width:width + 250] = color_bgr

                # Добавляем текст с процентом
                cv2.putText(result_img, f"{color_info['percentage']:.1f}%",
                            (width + 10, y_start + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

            # Сохранение
            save_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")],
                initialfile="dominant_color_result.jpg"
            )

            if save_path:
                cv2.imwrite(save_path, result_img)
                messagebox.showinfo("Успех", f"Результат сохранен в:\n{save_path}")
                self.status_var.set(f"Результат сохранен: {save_path.split('/')[-1]}")

    def clear_results(self):
        """Очистка предыдущих результатов"""
        self.figure.clear()
        self.canvas.draw()
        self.color_info.config(text="")
        self.dominant_color = None
        self.all_colors = None


def main():
    root = tk.Tk()
    app = DominantColorApp(root)

    # Центрирование окна на экране
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()