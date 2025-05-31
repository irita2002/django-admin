from networkx import NetworkXNoPath
import osmnx as ox
import networkx as nx
import folium
from shapely.geometry import Point

def generar_mapa_offline(ubicaciones, direccion_origen=None):
    # 1. Geocodifica o fija el origen
    if direccion_origen:
        punto_origen = ox.geocode(direccion_origen)
    else:
        punto_origen = (20.963422107542275, -76.96513045604253)
    lat0, lon0 = map(float, punto_origen)  # fuerza float

    # 2. Descarga grafo y projéctalo
    G = ox.graph_from_point((lat0, lon0), dist=1000, network_type='drive', simplify=True)
    G_proj = ox.project_graph(G)

    # 3. Proyecta el punto origen
    geom0, crs = ox.projection.project_geometry(Point(lon0, lat0), to_crs=G_proj.graph['crs'])
    x0, y0 = geom0.x, geom0.y

    # 4. Nodo origen
    nodo_origen = ox.distance.nearest_nodes(G_proj, x0, y0)

    resultados = []
    for loc in ubicaciones:
        try:
            # forza float y revisa tipos
            lat = float(loc.latitud)
            lon = float(loc.longitud)
        except Exception as e:
            print(f"[ERROR] al castear {loc.nombre}: lat={loc.latitud} ({type(loc.latitud)}), "
                  f"lon={loc.longitud} ({type(loc.longitud)}) → {e}")
            continue

        # proyecta el destino
        geom_d, _ = ox.projection.project_geometry(Point(lon, lat), to_crs=G_proj.graph['crs'])
        nodo_dest = ox.distance.nearest_nodes(G_proj, geom_d.x, geom_d.y)

        # intentar calcular la distancia
        try:
            dist = nx.shortest_path_length(G_proj, nodo_origen, nodo_dest, weight='length')
        except NetworkXNoPath:
            # si no hay camino, saltamos o le asignamos None
            # continue  # para omitir esta bodega
            dist = None  # o dist = float('inf')

        resultados.append({
            'loc': loc,
            'dist_m': dist,
        })

    # filtrar los que no tienen camino (opcional)
    resultados = [r for r in resultados if r['dist_m'] is not None]

    # 5. Ordena
    resultados_ordenados = sorted(resultados, key=lambda x: x['dist_m'])

    # 6. Dibuja mapa
    m = folium.Map(
        location=(lat0, lon0),
        zoom_start=15,
        tiles='OpenStreetMap',
        control_scale=True
    )
    # ¡Aquí el truco! forzamos el nombre de la variable JS:
    m.get_root().html.add_child(folium.Element(
        '<script>window.folium_map = map_{};</script>'.format(m._id)
    ))

    folium.Marker((lat0, lon0), tooltip="Tienda",
                  icon=folium.Icon(color='green')).add_to(m)
    for i, item in enumerate(resultados_ordenados, 1):
        l = item['loc']
        folium.Marker(
            (float(l.latitud), float(l.longitud)),
            tooltip=f"{i}. {l.nombre} — {item['dist_m']:.0f} m",
            icon=folium.Icon(color='blue')
        ).add_to(m)

    return m._repr_html_()