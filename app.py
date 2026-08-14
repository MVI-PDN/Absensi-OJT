import streamlit as st
import openpyxl
import pandas as pd
from openpyxl.styles import Font, Alignment, Border, Side
import io

st.set_page_config(page_title="Absensi OJT Digital", layout="wide", page_icon="📝")

def get_color_str(fill):
    """Mengekstrak kode warna dari sel Excel."""
    if not fill: return None
    if fill.fgColor:
        if fill.fgColor.type == 'rgb': return fill.fgColor.rgb
        elif fill.fgColor.type == 'indexed': return str(fill.fgColor.indexed)
    if fill.start_color and fill.start_color.index:
        return str(fill.start_color.index)
    return None

# --- Inisialisasi Session State ---
# Digunakan agar perubahan (tukar/pindah siswa) tersimpan selama aplikasi berjalan
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'weeks_data' not in st.session_state:
    st.session_state.weeks_data = {}
if 'students_data' not in st.session_state:
    st.session_state.students_data = {}

st.title("📝 Sistem Absensi OJT Digital (Advanced)")
st.write("Upload jadwal, kelola pertukaran siswa, dan isi absensi dengan opsi S/I/A.")

# ==========================================
# 1. UPLOAD & BACA FILE
# ==========================================
st.markdown("### 1. Upload Jadwal Induk")
uploaded_file = st.file_uploader("Upload file OJT 2026.xlsx di sini", type=["xlsx"])

if uploaded_file is not None and not st.session_state.data_loaded:
    with st.spinner("Membaca dan memetakan data..."):
        try:
            wb_source = openpyxl.load_workbook(uploaded_file, data_only=True)
            ws_source = wb_source['JADWAL']
            
            # 1a. Ekstrak Jadwal (Scan Kolom 9 dan 11 untuk mencari angka minggu)
            # Karena ada jadwal ganda (misal: minggu 1 dan 23 warnanya sama)
            weeks = {}
            for row in range(4, 60):
                for col in [9, 11]: # Scan kolom yg biasa berisi nomor minggu
                    cell = ws_source.cell(row=row, column=col)
                    if type(cell.value) in [int, float]:
                        c_str = get_color_str(cell.fill)
                        d_val = ws_source.cell(row=row, column=col+1).value
                        weeks[int(cell.value)] = {
                            'color': c_str,
                            'date': str(d_val) if d_val else "-"
                        }
            st.session_state.weeks_data = weeks

            # 1b. Ekstrak Data Siswa Dasar
            classes = {col: ws_source.cell(row=4, column=col).value for col in range(3, 8)}
            students = {}
            for row in range(5, 60):
                for col in range(3, 8):
                    cell = ws_source.cell(row=row, column=col)
                    val = str(cell.value).strip() if cell.value else ""
                    if len(val) > 2: # Pastikan bukan sel kosong
                        students[val] = {
                            'kelas': str(classes.get(col, '')).strip(),
                            'color': get_color_str(cell.fill)
                        }
            st.session_state.students_data = students
            st.session_state.data_loaded = True
            st.rerun() # Refresh untuk memunculkan UI selanjutnya
            
        except Exception as e:
            st.error(f"Error membaca file: {e}")

# Tombol reset jika ingin upload file baru
if st.session_state.data_loaded:
    if st.button("🔄 Reset & Upload File Lain"):
        st.session_state.data_loaded = False
        st.session_state.weeks_data = {}
        st.session_state.students_data = {}
        st.rerun()

# ==========================================
# 2. MANAJEMEN ABSENSI & SISWA
# ==========================================
if st.session_state.data_loaded:
    if not st.session_state.weeks_data:
        st.error("Jadwal mingguan tidak terdeteksi di file.")
    else:
        st.markdown("---")
        st.markdown("### 2. Kelola Jadwal & Absensi")
        
        # Opsi Minggu
        week_options = sorted(list(st.session_state.weeks_data.keys()))
        selected_week = st.selectbox("📅 Pilih Minggu Ke-:", week_options)
        
        target_color = st.session_state.weeks_data[selected_week]['color']
        target_date = st.session_state.weeks_data[selected_week]['date']
        
        st.info(f"**Periode OJT:** {target_date}")

        # --- FITUR TUKAR / PINDAH SISWA ---
        with st.expander("🛠️ Pertukaran / Pemindahan Jadwal Siswa", expanded=False):
            st.write("Gunakan fitur ini jika ada siswa yang pindah/tukar jadwal dari jadwal aslinya.")
            
            # Daftar semua siswa untuk dropdown
            all_student_names = sorted(list(st.session_state.students_data.keys()))
            
            col_tambah, col_tukar = st.columns(2)
            
            with col_tambah:
                st.markdown("**➡️ Masukkan Siswa ke Minggu Ini**")
                s_tambah = st.selectbox("Pilih Siswa:", ["-- Pilih Siswa --"] + all_student_names, key="add_s")
                if st.button("Tambahkan Siswa", type="secondary") and s_tambah != "-- Pilih Siswa --":
                    # Ubah warna/jadwal siswa tersebut menjadi warna minggu ini
                    st.session_state.students_data[s_tambah]['color'] = target_color
                    st.success(f"{s_tambah} berhasil dimasukkan ke jadwal ini!")
                    st.rerun()

            with col_tukar:
                st.markdown("**🔄 Tukar Jadwal (Siswa A ⇄ Siswa B)**")
                # Siswa A otomatis dari list minggu ini (untuk mempermudah)
                current_week_students = [name for name, data in st.session_state.students_data.items() if data['color'] == target_color]
                
                s_a = st.selectbox("Siswa A (Dari Minggu Ini):", ["-- Pilih Siswa A --"] + sorted(current_week_students), key="s_a")
                s_b = st.selectbox("Siswa B (Dari Minggu Lain):", ["-- Pilih Siswa B --"] + all_student_names, key="s_b")
                
                if st.button("Tukar Posisi") and s_a != "-- Pilih Siswa A --" and s_b != "-- Pilih Siswa B --":
                    # Tukar warna/jadwal mereka berdua
                    color_a = st.session_state.students_data[s_a]['color']
                    color_b = st.session_state.students_data[s_b]['color']
                    st.session_state.students_data[s_a]['color'] = color_b
                    st.session_state.students_data[s_b]['color'] = color_a
                    st.success(f"Posisi {s_a} dan {s_b} berhasil ditukar!")
                    st.rerun()

        # --- TABEL ABSENSI INTERAKTIF ---
        st.markdown("#### 📝 Tabel Absensi")
        st.caption("Klik pada sel hari (Senin-Jumat) untuk memilih opsi: ✔ (Hadir), S (Sakit), I (Izin), A (Alfa).")

        # Tarik siswa yang warnanya = warna target minggu ini
        active_students = [
            {"Nama Siswa": name, "Kelas": data['kelas']}
            for name, data in st.session_state.students_data.items()
            if data['color'] == target_color
        ]
        
        active_students.sort(key=lambda x: x['Kelas'])

        if not active_students:
            st.warning("Tidak ada siswa di minggu ini.")
        else:
            # Buat DataFrame
            df_data = []
            for idx, s in enumerate(active_students):
                df_data.append({
                    "NO": idx + 1,
                    "Nama Siswa": s['Nama Siswa'],
                    "Kelas": s['Kelas'],
                    "Senin": "✔",
                    "Selasa": "✔",
                    "Rabu": "✔",
                    "Kamis": "✔",
                    "Jumat": "✔",
                    "Keterangan": ""
                })
            
            df = pd.DataFrame(df_data)
            
            # Konfigurasi Pilihan Dropdown untuk Absensi
            opsi_absen = ["✔", "S", "I", "A", "-"]
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "NO": st.column_config.NumberColumn("NO", disabled=True, width="small"),
                    "Nama Siswa": st.column_config.TextColumn("Nama Siswa", disabled=True, width="medium"),
                    "Kelas": st.column_config.TextColumn("Kelas", disabled=True, width="small"),
                    "Senin": st.column_config.SelectboxColumn("Senin", options=opsi_absen, required=True),
                    "Selasa": st.column_config.SelectboxColumn("Selasa", options=opsi_absen, required=True),
                    "Rabu": st.column_config.SelectboxColumn("Rabu", options=opsi_absen, required=True),
                    "Kamis": st.column_config.SelectboxColumn("Kamis", options=opsi_absen, required=True),
                    "Jumat": st.column_config.SelectboxColumn("Jumat", options=opsi_absen, required=True),
                    "Keterangan": st.column_config.TextColumn("Keterangan Tambahan")
                },
                hide_index=True,
                use_container_width=True,
                height=min(40 * len(active_students) + 40, 600) # Tinggi dinamis
            )

            st.divider()

            # ==========================================
            # 3. GENERATE EXCEL OUTPUT
            # ==========================================
            st.markdown("### 3. Simpan Hasil Absensi")
            if st.button("💾 Generate & Download Excel", type="primary"):
                with st.spinner("Menyusun file Excel..."):
                    out_wb = openpyxl.Workbook()
                    out_ws = out_wb.active
                    out_ws.title = "ABSENSI REKAP"
                    
                    # Styles
                    bold_font = Font(bold=True)
                    center_align = Alignment(horizontal='center', vertical='center')
                    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                         top=Side(style='thin'), bottom=Side(style='thin'))
                    
                    # Header Info
                    out_ws['A1'] = "REKAP ABSENSI OJT SMK STRADA"
                    out_ws['A1'].font = Font(bold=True, size=12)
                    out_ws['A2'] = "Periode"; out_ws['C2'] = ":"; out_ws['D2'] = target_date
                    out_ws['A3'] = "Jadwal"; out_ws['C3'] = ":"; out_ws['D3'] = f"Minggu ke {selected_week}"
                    out_ws['A4'] = "Waktu"; out_ws['C4'] = ":"; out_ws['D4'] = "09:00 - 18:00"
                    out_ws['G2'] = "Hari Aktif"; out_ws['H2'] = 5
                    out_ws['G3'] = "Jumlah Siswa"; out_ws['H3'] = len(active_students)
                    
                    # Header Tabel
                    headers = [("NO", 1), ("Nama Siswa", 2), ("Kelas Jurusan", 3), ("Senin", 4), 
                               ("Selasa", 5), ("Rabu", 6), ("Kamis", 7), ("Jumat", 8), 
                               ("Kehadiran", 9), ("Jumlah Unit Dirakit", 10), ("KETERANGAN", 11)]
                    
                    for name, col_idx in headers:
                        c = out_ws.cell(row=6, column=col_idx, value=name)
                        c.font = bold_font; c.alignment = center_align; c.border = thin_border
                        
                    # Tulis Data Siswa
                    start_row = 7
                    for idx, row_data in edited_df.iterrows():
                        row = start_row + idx
                        
                        out_ws.cell(row=row, column=1, value=row_data['NO']).alignment = center_align
                        out_ws.cell(row=row, column=2, value=row_data['Nama Siswa'])
                        out_ws.cell(row=row, column=3, value=row_data['Kelas']).alignment = center_align
                        
                        total_hadir = 0
                        days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat']
                        
                        # Loop kolom hari
                        for col_offset, day in enumerate(days):
                            col_idx = 4 + col_offset
                            status = row_data[day]
                            
                            # Tulis status (✔, S, I, A, -) ke dalam sel
                            out_ws.cell(row=row, column=col_idx, value=status).alignment = center_align
                            
                            # Hitung kehadiran (Hanya dihitung jika statusnya ✔)
                            if status == "✔":
                                total_hadir += 1
                        
                        # Tulis Total Kehadiran
                        out_ws.cell(row=row, column=9, value=total_hadir).alignment = center_align
                        
                        # Kosongkan Kolom Unit
                        out_ws.cell(row=row, column=10, value="")
                        
                        # Tulis Keterangan Bebas
                        ket_val = str(row_data['Keterangan']) if pd.notna(row_data['Keterangan']) else ""
                        out_ws.cell(row=row, column=11, value=ket_val)
                        
                        # Aplikasikan border
                        for c_idx in range(1, 12):
                            out_ws.cell(row=row, column=c_idx).border = thin_border

                    # Lebar Kolom
                    out_ws.column_dimensions['A'].width = 5
                    out_ws.column_dimensions['B'].width = 35
                    out_ws.column_dimensions['C'].width = 15
                    for col in ['D', 'E', 'F', 'G', 'H', 'I']: 
                        out_ws.column_dimensions[col].width = 10
                    out_ws.column_dimensions['J'].width = 18
                    out_ws.column_dimensions['K'].width = 35
                    
                    # Simpan File ke Memori
                    buffer = io.BytesIO()
                    out_wb.save(buffer)
                    buffer.seek(0)
                    
                    st.success("✅ File Excel siap diunduh!")
                    
                    st.download_button(
                        label=f"📥 Download Absensi Minggu {selected_week} (Hasil)",
                        data=buffer,
                        file_name=f"Absensi_OJT_Minggu_{selected_week}_Final.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
