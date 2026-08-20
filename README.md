# İzmir · Güzelyalı haritası

[prettymaps](https://github.com/marceloprates/prettymaps) ile İzmir'in Güzelyalı
(Konak) semtinin OpenStreetMap verisinden stilize haritasını üretir.

## Kurulum

```bash
pip install -r requirements.txt
```

`pip install prettymaps` çözümlemesi takılırsa (paketin `numpy<1.25` pini
yüzünden olabiliyor), bağımlılıkları önce kurup prettymaps'i tek başına almak
işi hızlandırır:

```bash
pip install osmnx'<2.0' geopandas shapely matplotlib scipy networkx \
            opencv-python-headless scikit-image rioxarray vsketch tqdm
pip install --no-deps prettymaps==1.4.2
```

## Çalıştırma

```bash
python guzelyali_izmir.py                    # Ege paleti, 1100 m yarıçap
python guzelyali_izmir.py --palette gece     # koyu tema
python guzelyali_izmir.py --radius 1600      # daha geniş alan
python guzelyali_izmir.py --out guzelyali.png --dpi 400
```

Çıktı, çalıştırılan dizine `guzelyali_izmir_<palet>_<yarıçap>m.png` olarak yazılır.

## Parametreler

| Bayrak | Varsayılan | Açıklama |
| --- | --- | --- |
| `--lat` / `--lon` | `38.4022`, `27.0705` | Merkez koordinat (Güzelyalı İskelesi civarı) |
| `--query` | yok | Yer adıyla çalışmak için (ör. `"Güzelyalı, Konak, İzmir, Türkiye"`) |
| `--radius` | `1100` | Metre cinsinden yarıçap |
| `--palette` | `ege` | `ege` (gündüz) veya `gece` (koyu) |
| `--out` | otomatik | Çıktı dosyası |
| `--dpi` | `300` | Çözünürlük |
| `--no-title` | — | Başlık/altyazıyı gizler |
| `--skip-check` | — | OSM erişim ön kontrolünü atlar |

Varsayılan olarak yer adı yerine **koordinat** kullanılır: Türkiye'de Çanakkale
ve Bursa/Mudanya dahil birden fazla "Güzelyalı" olduğu için geocode sonucu
yanlış semte düşebiliyor. Yer adıyla denemek isterseniz `--query` kullanın.

## Katmanlar

`streets`, `building`, `sea`, `water`, `green`, `beach`, `parking`
(iskele/yaya alanları dahil). Deniz için prettymaps'in `sea` katmanı kullanılır:
İzmir Körfezi, `natural=coastline` çizgilerinden poligona dönüştürülür — kapalı
su poligonu olmayan kıyılarda denizin boş kalmasını bu önler.

## Ağ gereksinimi

Veri çalışma anında OpenStreetMap'ten çekilir:

- `overpass-api.de` — harita verisi (zorunlu)
- `nominatim.openstreetmap.org` — yalnızca `--query` ile geocode için

Script çizime başlamadan önce bu adresleri yoklar. Erişim yoksa **boş bir görsel
üretmek yerine** hata verip çıkar (çıkış kodu `2`); osmnx erişemediği katmanları
sessizce boş geçtiği için bu kontrol önemlidir. Veri geldiği hâlde tüm katmanlar
boş kalırsa çıkış kodu `3` olur.

## GitHub Actions ile otomatik üretim (bilgisayar gerekmeden)

`.github/workflows/build-map.yml`, her `*.py` değişikliğinde GitHub runner'ında
haritayı üretir; runner'ın OpenStreetMap erişimi olduğu için Overpass'a çıkamayan
ortamlarda da sonuç alınır. İş akışı:

1. Bağımlılıkları kurar (prettymaps `--no-deps` ile, çözümleme kilitlenmesin diye),
2. `ege` ve `gece` paletlerinde iki harita çizer,
3. PNG'leri `site/` altına depoya işler,
4. `site/`'ı **GitHub Pages**'te yayımlar ve iş çıktısı (artifact) olarak yükler.

Elle çalıştırmak için: Actions sekmesi > "Güzelyalı haritası" > Run workflow.

## İnternet erişimi olmayan ortamlar

Overpass'a çıkılamıyorsa harita yerel bir OSM dosyasından çizilebilir:

```bash
# openstreetmap.org > Export ile alanı .osm olarak indirin, ya da bir .osm.pbf kullanın
python guzelyali_from_file.py guzelyali.osm --radius 1100 --palette ege
```

Desteklenen kaynaklar: `.osm` (XML), `.osm.pbf`, `.geojson`, `.gpkg`.
Okuma GDAL'ın OSM sürücüsüyle (pyogrio) yapılır; etiketler hem ayrı sütunlardan
hem de `other_tags` alanından okunur. Deniz, `natural=coastline` çizgisinin sınır
kutusunu ikiye bölmesi ve yol ağıyla kesişmeyen parçanın deniz sayılması
yöntemiyle üretilir (prettymaps'in yaklaşımı); dosyanın kenarında biten kıyı
çizgileri kutuyu bölebilsin diye uçlarından uzatılır.

İlgili dosyalar: `osm_extract.py` (okuma/filtreleme/kırpma), `render.py` (çizim).

## Test

Ağ gerektirmeyen duman testi — paletlerin ve katman stillerinin matplotlib
tarafından kabul edildiğini sentetik geometriyle doğrular:

```bash
python tests/test_styles.py          # palet/stil duman testi
python tests/test_offline_render.py  # sentetik .osm -> PNG, uçtan uca
```

## Lisans / atıf

Harita verisi © OpenStreetMap katılımcıları (ODbL). Çizim motoru: prettymaps
(Marcelo Prates, AGPL-3.0).
