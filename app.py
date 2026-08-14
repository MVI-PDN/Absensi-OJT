import streamlit as st
import openpyxl
import pandas as pd
from openpyxl.styles import Font, Alignment, Border, Side
import io

# Konfigurasi Halaman Website agar lebih lebar (untuk menampung tabel)
st.set_page_config(page_title="Absensi OJT Digital", layout="wide", page_icon="📝")

def get_color_str(fill):
    if not fill: return None
    if fill.fgColor:
        if fill.fgColor.type == 'rgb': return fill.fgColor.rgb
        elif fill.fgColor.type == 'indexed': return str(fill.fgColor.indexed)
    if fill.start_color and fill.start_color.index:
        return str(fill.start_color.index)
    return None

st.title("📝 Sistem Absensi OJT Digital")
st.write("Upload Jadwal Induk, pilih minggu, lalu isi absensi siswa langsung di website ini.")

# 1. Upload File
st.markdown("### 1. Upload Jadwal Induk")
uploaded_file = st.file_uploader("Upload file OJT 2026.xlsx di sini", type=["xlsx"])

if uploaded_file is not None:
    try:
        wb_source = openpyxl.load_workbook(uploaded_file, data_only=True)
        if 'JADWAL' not in wb_source.sheetnames:
            st.error("❌ Error: Sheet 'JADWAL' tidak ditemukan!")
        else:
            ws_source = wb_source['JADWAL']
            
            # Ekstrak Jadwal
            weeks_data = {}
            for row in range(4, 30):
                for col in range(9, 13):
                    cell = ws_source.cell(row=row, column=col)
                    if cell.value and isinstance(cell.value, (int, float)):
                        color_str = get_color_str(cell.fill)
                        date_range = ws_source.cell(row=row, column=col+1).value
                        weeks_data[int(cell.value)] = {
                            'color': color_str,
                            'date': str(date_range) if date_range else "Tanggal tidak tercantum"
                        }
            
            if not weeks_data:
                st.warning("⚠️ Tidak dapat mendeteksi jadwal mingguan.")
            else:
                st.markdown("### 2. Pilih Jadwal & Isi Absensi")
                
                # Menggunakan layout kolom
                col1, col2 = st.columns([1, 2])
                with col1:
                    week_options = sorted(list(weeks_data.keys()))
                    selected_week = st.selectbox("Pilih Minggu Ke-:", week_options)
                    target_color = weeks_data[selected_week]['color']
                    target_date = weeks_data[selected_week]['date']
                    
                    st.info(f"**Tanggal:** {target_date}")

                # Ekstrak Siswa berdasarkan minggu terpilih
                classes = {col: ws_source.cell(row=4, column=col).value for col in range(3, 8)}
                students = []
                for row in range(5, 55):
                    for col in range(3, 8):
                        cell = ws_source.cell(row=row, column=col)
                        if cell.value and isinstance(cell.value, str) and len(cell.value) > 2:
                            if get_color_str(cell.fill) == target_color:
                                students.append({
                                    'Nama Siswa': str(cell.value).strip(),
                                    'Kelas': str(classes.get(col, '')).strip()
                                })
                
                if not students:
                    st.error("Siswa tidak ditemukan untuk minggu ini.")
                else:
                    students.sort(key=lambda x: x['Kelas'])
                    
                    # --- MEMBUAT DATAFRAME UNTUK TABEL INTERAKTIF ---
                    # Membuat data awal (default Hadir/True)
                    df_data = []
                    for idx, s in enumerate(students):
                        df_data.append({
                            "NO": idx + 1,
                            "Nama Siswa": s['Nama Siswa'],
                            "Kelas": s['Kelas'],
                            "Senin": True,
                            "Selasa": True,
                            "Rabu": True,
                            "Kamis": True,
                            "Jumat": True,
                            "Keterangan": ""
                        })
                    
                    df = pd.DataFrame(df_data)
                    
                    st.markdown("#### Tabel Absensi (Bisa di-edit langsung)")
                    st.caption("Petunjuk: Centang kotak jika Hadir. Hilangkan centang jika tidak hadir. Ketik di kolom Keterangan untuk alasan (Sakit/Izin).")
                    
                    # --- MENAMPILKAN TABEL YANG BISA DI-EDIT (DATA EDITOR) ---
                    # Menyimpan hasil editan user ke dalam variabel `edited_df`
                    edited_df = st.data_editor(
                        df,
                        column_config={
                            "NO": st.column_config.NumberColumn("NO", disabled=True),
                            "Nama Siswa": st.column_config.TextColumn("Nama Siswa", disabled=True),
                            "Kelas": st.column_config.TextColumn("Kelas", disabled=True),
                            "Senin": st.column_config.CheckboxColumn("Senin", default=True),
                            "Selasa": st.column_config.CheckboxColumn("Selasa", default=True),
                            "Rabu": st.column_config.CheckboxColumn("Rabu", default=True),
                            "Kamis": st.column_config.CheckboxColumn("Kamis", default=True),
                            "Jumat": st.column_config.CheckboxColumn("Jumat", default=True),
                            "Keterangan": st.column_config.TextColumn("Keterangan (S/I/A)")
                        },
                        hide_index=True,
                        use_container_width=True,
                        height=500 # Tinggi tabel
                    )
                    
                    st.divider()
                    
                    # --- TOMBOL GENERATE EXCEL DARI DATA YANG DIEDIT ---
                    st.markdown("### 3. Simpan Hasil Absensi")
                    if st.button("💾 Generate File Excel Absensi", type="primary"):
                        with st.spinner("Membuat file Excel..."):
                            out_wb = openpyxl.Workbook()
                            out_ws = out_wb.active
                            out_ws.title = "ABSENSI REKAP"
                            
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
                                
                            # Memasukkan Data dari Tabel Interaktif ke Excel
                            start_row = 7
                            for idx, row_data in edited_df.iterrows():
                                row = start_row + idx
                                
                                # No, Nama, Kelas
                                out_ws.cell(row=row, column=1, value=row_data['NO']).alignment = center_align
                                out_ws.cell(row=row, column=2, value=row_data['Nama Siswa'])
                                out_ws.cell(row=row, column=3, value=row_data['Kelas']).alignment = center_align
                                
                                # Menghitung Kehadiran
                                total_hadir = 0
                                days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat']
                                
                                for col_offset, day in enumerate(days):
                                    col_idx = 4 + col_offset
                                    is_hadir = row_data[day]
                                    
                                    # Jika dicentang (True), beri tanda '✔', jika tidak beri '-'
                                    mark = '✔' if is_hadir else '-'
                                    if is_hadir:
                                        total_hadir += 1
                                        
                                    out_ws.cell(row=row, column=col_idx, value=mark).alignment = center_align
                                
                                # Total Kehadiran
                                out_ws.cell(row=row, column=9, value=total_hadir).alignment = center_align
                                
                                # Kosongkan kolom Unit (bisa diisi manual nanti)
                                out_ws.cell(row=row, column=10, value="")
                                
                                # Masukkan Keterangan
                                out_ws.cell(row=row, column=11, value=str(row_data['Keterangan']) if pd.notna(row_data['Keterangan']) else "")
                                
                                # Pasang Border untuk seluruh baris
                                for c_idx in range(1, 12):
                                    out_ws.cell(row=row, column=c_idx).border = thin_border

                            # Mengatur Lebar Kolom
                            out_ws.column_dimensions['A'].width = 5
                            out_ws.column_dimensions['B'].width = 35
                            out_ws.column_dimensions['C'].width = 15
                            for col in ['D', 'E', 'F', 'G', 'H', 'I']: 
                                out_ws.column_dimensions[col].width = 10
                            out_ws.column_dimensions['J'].width = 18
                            out_ws.column_dimensions['K'].width = 35
                            
                            buffer = io.BytesIO()
                            out_wb.save(buffer)
                            buffer.seek(0)
                            
                            st.success("✅ File Excel berhasil dibuat dengan data absensi terbaru!")
                            
                            st.download_button(
                                label=f"📥 Download Absensi Minggu {selected_week}",
                                data=buffer,
                                file_name=f"Absensi_OJT_Minggu_{selected_week}_Terisi.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
