import requests, os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

class PixivDownloaderApp:
    def __init__(self, root:tk.Tk) -> None:
        self.window = root # 'root' chính là cái cửa sổ tk.Tk() được truyền vào
        self.window.title("Pixiv Downloader 🎨")
        self.window.geometry("1280x720")

        # Cấu hình headers của request
        self.headers = {
            "Referer": "https://www.pixiv.net/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }

        # Tạo Label hướng dẫn nhập ID hoặc URL
        self.label_id_or_url = tk.Label(self.window, text="Nhập Pixiv ID hoặc URL:")
        self.label_id_or_url.pack(pady=(10, 0)) # pady là khoảng cách đệm trên/dưới

        # Tạo ô input để nhập ID - URL
        self.entry_id_or_url = tk.Entry(self.window, width=100)
        self.entry_id_or_url.pack(pady=(0, 10))

        # Tạo Button hướng dẫn nhập đường dẫn lưu file
        self.btn_select_dir_path = tk.Button(self.window, text="Chọn vị trí lưu ảnh:", command=self.select_dir_path)
        self.btn_select_dir_path.pack(pady=(10, 0))

        # Tạo ô nhập đường dẫn lưu file
        self.entry_dir_path = tk.Entry(self.window, width=100)
        self.entry_dir_path.pack(pady=(0, 10))

        # Nút tải xuống
        self.btn_download = tk.Button(self.window, text="Tải xuống", command=self.start_download_thread)
        self.btn_download.pack(pady=10)

        # Label ghi lại quá trình tải, ban đầu là "Chưa hiển thị gì cả (rỗng)"
        self.label_log = tk.Label(self.window, text="")
        self.label_log.pack(pady=(10, 0))

    def select_dir_path(self):
        dir_path = filedialog.askdirectory()
        self.entry_dir_path.delete(0, tk.END)
        self.entry_dir_path.insert(0, dir_path)

    def download(self):
        # 1. Lấy ID/URL từ ô nhập liệu
        artwork_id_or_url:str = self.entry_id_or_url.get()

        # 2. Lấy thư mục lưu
        dir_path:str = self.entry_dir_path.get()

        # 3. Kiểm tra đầu vào: xem người dùng có chọn thư mục và có nhập ID hay không
        if not artwork_id_or_url or not dir_path:
            self.btn_download.config(state=tk.NORMAL, text="Tải xuống")
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ID và chọn thư mục!")
            return # Dừng hàm tại đây nếu thiếu dữ liệu
        
        # -------------------- Xử lý ID ---------------------
        # Xóa dấu / dư ở 2 đầu (nếu có)
        # Tách lấy phần tử cuối cùng
        # Xóa phần tham số sau dấu ?
        artwork_id = artwork_id_or_url.strip("/").split("/").pop().split("?")[0]
        print(f"ID: {artwork_id} - Lưu tại: {dir_path}")

        try:
            # 4. Gọi API
            self.label_log.config(text="Đang kết nối...")
            api_url = f"https://www.pixiv.net/ajax/illust/{artwork_id}/pages"
            response = requests.get(api_url, headers=self.headers, timeout=10) # Sau 10 giây không nhận phản hồi thì ném ra lỗi
            response.raise_for_status() # Tự động báo lỗi nếu status code không phải 200
            
            # 5. Tạo thư mục để lưu ảnh nếu request thành công thì 
            os.makedirs(dir_path, exist_ok=True)

            # 6. Tải từng ảnh
            imgs:list = response.json()["body"]
            for i, img in enumerate(imgs, 1):
                # lấy URL của ảnh
                original_img_url = img["urls"]["original"]
                file_name = original_img_url.split("/").pop()
                full_path = os.path.join(dir_path, file_name) # Dùng os.path.join để nối đường dẫn chuẩn theo hệ điều hành
                
                # Tải nội dung ảnh
                img_content = requests.get(original_img_url, headers=self.headers, timeout=10).content
                
                # Ghi dữ liệu vào file ảnh
                with open(full_path, mode="wb") as file_img:
                    file_img.write(img_content)

                # Cập nhật giao diện
                print(f"Đã tải xong: {file_name}")
                self.label_log.config(text=f"Đang tải ảnh {i}/{len(imgs)}...")

            self.label_log.config(text="Hoàn tất!")
            messagebox.showinfo("Thành công", f"Đã tải xong {len(imgs)} ảnh!")
            
        # --- CÁC TẦNG BẢO VỆ ---
        
        # Tầng 1: Lỗi mạng (Rớt mạng, Timeout, Link hỏng...)
        except requests.exceptions.RequestException as e:
            print(f"Lỗi mạng: {e}")
            messagebox.showerror("Lỗi kết nối", "Không thể tải dữ liệu. Vui lòng kiểm tra mạng hoặc ID ảnh, URL Pixiv.")

        # Tầng 2: Lỗi File (Ổ cứng đầy, không có quyền ghi...)
        except OSError as e:
            print(f"Lỗi ghi file: {e}")
            messagebox.showerror("Lỗi File", f"Không thể lưu file. Có thể do ổ cứng đầy hoặc lỗi quyền hạn.\nChi tiết: {e}")

        # Tầng 3: Lỗi lạ (Code bị bug, dữ liệu trả về sai định dạng...)
        except Exception as e:
            print(f"Lỗi không xác định: {e}")
            messagebox.showerror("Lỗi Lạ", f"Đã xảy ra lỗi không mong muốn:\n{e}")

        finally:
            # Đưa nút tải xuống về trạng thái bình thường bất kể tải được hay lỗi
            self.btn_download.config(state=tk.NORMAL, text="Tải xuống")
    # Hàm tạo một luồng phụ (worker thread), có nhiệm vụ chạy hàm download (song song với luồng chính chạy chương trình) tải file ảnh
    def start_download_thread(self):
        # 1. Khóa nút lại ngay lập tức khi "tải xuống" và đổi chữ cho ngầu
        self.btn_download.config(state=tk.DISABLED, text="Đang tải...")

        download_thread = threading.Thread(target=self.download)
        download_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = PixivDownloaderApp(root)
    app.window.mainloop()