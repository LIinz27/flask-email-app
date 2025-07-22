# Deploy Flask Email App - GRATIS

## 🚀 Platform Gratis yang Direkomendasikan

### 1. Railway (PALING MUDAH) ⭐
**Gratis**: 500 jam/bulan + Database MySQL gratis

**Langkah-langkah:**
1. Daftar di [Railway.app](https://railway.app)
2. Connect dengan GitHub account
3. Push kode ke GitHub repo
4. Di Railway: "New Project" → "Deploy from GitHub repo"
5. Pilih repo ini
6. Railway akan auto-deploy!

**Environment Variables yang dibutuhkan:**
- `FLASK_ENV` = `production`

### 2. Render (ALTERNATIF BAGUS) ⭐
**Gratis**: Web service + PostgreSQL gratis

**Langkah-langkah:**
1. Daftar di [Render.com](https://render.com)
2. Connect dengan GitHub
3. "New Web Service" → pilih repo
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### 3. Heroku (TERBATAS)
**Gratis**: 550 jam/bulan (dengan verifikasi kartu)

## 📋 Persiapan Sebelum Deploy

1. **Push ke GitHub:**
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. **Setup Database:**
   - Railway: Otomatis dapat MySQL
   - Render: Dapat PostgreSQL gratis
   - Heroku: Addon JawsDB MySQL

## 🔧 File yang Sudah Disiapkan

- ✅ `Procfile` - Untuk Heroku
- ✅ `runtime.txt` - Specify Python version
- ✅ `requirements.txt` - Dependencies dengan versi
- ✅ `railway.json` - Railway config
- ✅ `render.yaml` - Render config
- ✅ `config.py` - Auto-detect environment

## 🎯 Rekomendasi: GUNAKAN RAILWAY

Railway paling mudah karena:
- Setup database otomatis
- Deploy langsung dari GitHub
- Monitoring built-in
- Gratis 500 jam (cukup untuk 1 bulan non-stop)

## 📞 Butuh Bantuan?

Jika ada error saat deploy, kirimkan screenshot error-nya!
