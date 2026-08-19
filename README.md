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

## Test

Ağ gerektirmeyen duman testi — paletlerin ve katman stillerinin matplotlib
tarafından kabul edildiğini sentetik geometriyle doğrular:

```bash
python tests/test_styles.py
```

## Lisans / atıf

Harita verisi © OpenStreetMap katılımcıları (ODbL). Çizim motoru: prettymaps
(Marcelo Prates, AGPL-3.0).
