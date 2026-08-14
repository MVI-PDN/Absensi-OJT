import streamlit as st
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
import io

# Konfigurasi Halaman Website
st.set_page_config(page_title="Generator Absensi OJT", layout="centered", page_icon="⚙️")

def get_color_str(fill):
    """
    Fungsi khusus untuk mengekstrak kode warna dari sel Excel.
    Menangani berbagai cara openpyxl menyimpan format warna.
    """
    if not fill: return None
    if fill.fgColor:
        if fill.fgColor.type == 'rgb': return fill.fgColor.rgb
        elif fill.fgColor.type == 'indexed': return str(fill.fgColor.indexed)
    if fill.start_color and fill.start_color.index:
        return str(fill.start_color.index)
    return None

# Judul dan Deskripsi Web
st.title("⚙️ Auto-Generate Absensi OJT")
st.write("Aplikasi ini membaca file Jadwal Induk (warna blok) untuk membuat template absensi mingguan secara otomatis.")

# Fitur Upload File
st.markdown("### 1. Upload Jadwal Induk")
uploaded_file = st.file_uploader("Upload file OJT 2026.xlsx di sini", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Load workbook dari file yang diupload
        wb_source = openpyxl.load_workbook(uploaded_file, data_only=True)
        
        # Validasi apakah Sheet 'JADWAL' ada
        if 'JADWAL' not in wb_source.sheetnames:
            st.error("❌ Error: Tidak menemukan sheet bernama 'JADWAL'. Pastikan file yang diupload benar.")
        else:
            ws_source = wb_source['JADWAL']
            st.success("✅ File berhasil dibaca!")
            
            # --- PROSES 1: EKSTRAKSI JADWAL & WARNA ---
            st.markdown("### 2. Pilih Minggu")
            weeks_data = {}
            
            # Scanning area jadwal (Baris 4-30, Kolom 9-12)
            for row in range(4, 30):
                for col in range(9, 13):
                    cell = ws_source.cell(row=row, column=col)
                    # Jika sel berisi angka (menandakan minggu ke-X)
                    if cell.value and isinstance(cell.value, (int, float)):
                        color_str = get_color_str(cell.fill)
                        # Ambil tanggal di sebelah kanan nomor minggu
                        date_range = ws_source.cell(row=row, column=col+1).value
                        weeks_data[int(cell.value)] = {
                            'color': color_str,
                            'date': str(date_range) if date_range else "Tanggal tidak tercantum"
                        }
            
            if not weeks_data:
                st.warning("⚠️ Tidak dapat mendeteksi jadwal mingguan. Pastikan format tabel di sebelah kanan sesuai.")
            else:
                # Mengurutkan opsi dropdown dari minggu terkecil ke terbesar
                week_options = sorted(list(weeks_data.keys()))
                selected_week = st.selectbox("Pilih Jadwal Minggu Ke-:", week_options)
                
                # Tombol Eksekusi
                if st.button("🚀 Generate Template Absensi", type="primary"):
                    with st.spinner(f"Sedang memproses data untuk Minggu ke-{selected_week}..."):
                        
                        target_color = weeks_data[selected_week]['color']
                        target_date = weeks_data[selected_week]['date']
                        
                        # --- PROSES 2: EKSTRAKSI NAMA SISWA BERDASARKAN WARNA ---
                        # Ambil nama kelas di Baris 4 (Kolom C-G)
                        classes = {}
                        for col in range(3, 8):
                            classes[col] = ws_source.cell(row=4, column=col).value
                            
                        # Scan nama siswa di Baris 5-55 (Kolom C-G)
                        students = []
                        for row in range(5, 55):
                            for col in range(3, 8):
                                cell = ws_source.cell(row=row, column=col)
                                # Pastikan sel berisi teks nama (bukan angka/kosong)
                                if cell.value and isinstance(cell.value, str) and len(cell.value) > 2:
                                    if get_color_str(cell.fill) == target_color:
                                        students.append({
                                            'name': str(cell.value).strip(),
                                            'class': str(classes.get(col, '')).strip()
                                        })
                        
                        if not students:
                            st.error(f"❌ Tidak ada siswa yang ditemukan untuk Minggu ke-{selected_week}. (Warna jadwal mungkin tidak cocok dengan warna blok siswa).")
                        else:
                            # Urutkan siswa berdasarkan kelas
                            students.sort(key=lambda x: x['class'])
                            
                            # --- PROSES 3: PEMBUATAN FILE EXCEL BARU (OUTPUT) ---
                            out_wb = openpyxl.Workbook()
                            out_ws = out_wb.active
                            out_ws.title = "ABSENSI REKAP"
                            
                            # Konfigurasi Gaya (Styling)
                            bold_font = Font(bold=True)
                            center_align = Alignment(horizontal='center', vertical='center')
                            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                                 top=Side(style='thin'), bottom=Side(style='thin'))
                            
                            # Header Atas
                            out_ws['A1'] = "REKAP ABSENSI OJT SMK STRADA"
                            out_ws['A1'].font = Font(bold=True, size=12)
                            out_ws['A2'] = "Periode"; out_ws['C2'] = ":"; out_ws['D2'] = target_date
                            out_ws['A3'] = "Jadwal"; out_ws['C3'] = ":"; out_ws['D3'] = f"Minggu ke {selected_week}"
                            out_ws['A4'] = "Waktu"; out_ws['C4'] = ":"; out_ws['D4'] = "09:00 - 18:00"
                            out_ws['G2'] = "Hari Aktif"; out_ws['H2'] = 5
                            out_ws['G3'] = "Jumlah Siswa"; out_ws['H3'] = len(students)
                            
                            # Header Tabel
                            headers = [("NO", 1), ("Nama Siswa", 2), ("Kelas Jurusan", 3), ("Senin", 4), 
                                       ("Selasa", 5), ("Rabu", 6), ("Kamis", 7), ("Jumat", 8), 
                                       ("Kehadiran", 9), ("Jumlah Unit Dirakit", 10), ("KETERANGAN", 11)]
                            
                            for name, col_idx in headers:
                                c = out_ws.cell(row=6, column=col_idx, value=name)
                                c.font = bold_font; c.alignment = center_align; c.border = thin_border
                                
                            # Mengisi Data Siswa
                            start_row = 7
                            for idx, s in enumerate(students):
                                row = start_row + idx
                                # No, Nama, Kelas
                                c1 = out_ws.cell(row=row, column=1, value=idx + 1)
                                c1.alignment = center_align; c1.border = thin_border
                                
                                c2 = out_ws.cell(row=row, column=2, value=s['name'])
                                c2.border = thin_border
                                
                                c3 = out_ws.cell(row=row, column=3, value=s['class'])
                                c3.alignment = center_align; c3.border = thin_border
                                
                                # Centang Hadir (Senin-Jumat)
                                for col in range(4, 9):
                                    c = out_ws.cell(row=row, column=col, value='✔')
                                    c.alignment = center_align; c.border = thin_border
                                    
                                # Total Kehadiran
                                c9 = out_ws.cell(row=row, column=9, value=5)
                                c9.alignment = center_align; c9.border = thin_border
                                
                                # Kolom Kosong dengan Border
                                out_ws.cell(row=row, column=10).border = thin_border
                                out_ws.cell(row=row, column=11).border = thin_border

                            # Mengatur Lebar Kolom
                            out_ws.column_dimensions['A'].width = 5
                            out_ws.column_dimensions['B'].width = 35
                            out_ws.column_dimensions['C'].width = 15
                            for col in ['D', 'E', 'F', 'G', 'H', 'I']: 
                                out_ws.column_dimensions[col].width = 10
                            out_ws.column_dimensions['J'].width = 18
                            out_ws.column_dimensions['K'].width = 35
                            
                            # --- PROSES 4: PENYIAPAN FILE UNTUK DOWNLOAD ---
                            buffer = io.BytesIO()
                            out_wb.save(buffer)
                            buffer.seek(0)
                            
                            st.success(f"✅ Selesai! Berhasil membuat absensi untuk {len(students)} siswa.")
                            
                            # Tombol Download
                            st.download_button(
                                label=f"📥 Download Absensi Minggu {selected_week}",
                                data=buffer,
                                file_name=f"Absensi_OJT_Minggu_{selected_week}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
