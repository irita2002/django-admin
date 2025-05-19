import osmnx as ox
import folium

def generar_mapa_offline(ubicaciones):
    # Obtener red vial local
    G = ox.graph_from_address(
            'Tu Ciudad Principal', 
            dist=1000,  # Radio en metros
            network_type='drive',
            simplify=True
        )
    
    # Crear mapa base
    m = folium.Map(
            location=[ubicaciones[0].latitud, ubicaciones[0].longitud],
            zoom_start=16,
            tiles='cartodbpositron'
        )
    
    # Añadir ubicaciones
    for loc in ubicaciones:
            folium.Marker(
                [loc.latitud, loc.longitud],
                popup=f"<b>{loc.nombre}</b>",
                icon=folium.Icon(color='blue')
            ).add_to(m)
    
    return m._repr_html_()