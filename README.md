# İzmir · Güzelyalı haritası

[prettymaps](https://github.com/marceloprates/prettymaps) kullanarak İzmir'in
Güzelyalı semtinin (Konak) OpenStreetMap verisinden stilize haritasını üretir.

## Kurulum

```bash
pip install -r requirements.txt
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
| `--query` | yok | Yer adı ile geocode (ör. `"Güzelyalı, Konak, İzmir, Türkiye"`) |
| `--radius` | `1100` | Metre cinsinden yarıçap |
| `--palette` | `ege` | `ege` (gündüz) veya `gece` (koyu) |
| `--dpi` | `300` | Çıktı çözünürlüğü |
| `--no-title` | — | Başlık/altyazıyı gizler |

Varsayılan olarak yer adı yerine **koordinat** kullanılır: Türkiye'de Çanakkale
ve Bursa/Mudanya dahil birden fazla "Güzelyalı" bulunduğu için geocode sonucu
yanlış semte düşebiliyor. Yer adıyla denemek isterseniz `--query` bayrağını
kullanın.

## Ağ gereksinimi

Veri çalışma anında OpenStreetMap'ten çekilir; şu adreslere erişim gerekir:

- `overpass-api.de` (harita verisi)
- `nominatim.openstreetmap.org` (yalnızca `--query` ile geocode için)

Bu adresler kapalıysa script, ağ hatasını açık bir mesajla bildirip çıkar.

## Kıyı şeridi notu

İzmir Körfezi OSM'de yer yer `natural=coastline` çizgileriyle modellenir; kapalı
bir su poligonu bulunmayan bölgelerde deniz alanı boş kalabilir. Script `water`
katmanında `natural=water|bay|strait|coastline` ve `place=sea` etiketlerinin
hepsini toplar; yine de boş kalırsa `--radius` değerini büyütmek genelde körfez
poligonunu kapsama alır.

## Lisans / atıf

Harita verisi © OpenStreetMap katılımcıları (ODbL). Çizim motoru:
prettymaps (Marcelo Prates, AGPL-3.0).
