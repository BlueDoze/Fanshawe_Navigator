import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const API_URL = 'http://localhost:8000';

// Component to fit map bounds
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

export default function MapView({ currentRoute, onBuildingClick, selectedBuilding }) {
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [mapBounds, setMapBounds] = useState(null);
  const [buildingLayers, setBuildingLayers] = useState({});

  useEffect(() => {
    loadGeoJSON();
  }, []);

  const loadGeoJSON = async () => {
    try {
      const response = await fetch(`${API_URL}/api/geojson`);
      const data = await response.json();
      setGeoJsonData(data);

      // Calculate bounds
      if (data && data.features && data.features.length > 0) {
        const bounds = L.geoJSON(data).getBounds();
        setMapBounds(bounds);
      }
    } catch (error) {
      console.error('Error loading GeoJSON:', error);
    }
  };

  const getBuildingStyle = (feature) => {
    const props = feature.properties;
    const isCollege = props.operator === 'Fanshawe College' || 
                     props.name?.includes('Fanshawe') || 
                     props.ref;

    let fillColor = isCollege ? '#764ba2' : '#bdc3c7';
    let fillOpacity = isCollege ? 0.3 : 0.1;
    let weight = isCollege ? 3 : 2;

    // Highlight buildings in current route
    if (currentRoute && props.ref) {
      if (props.ref === currentRoute.origem) {
        fillColor = '#27ae60';
        fillOpacity = 0.7;
        weight = 4;
      } else if (props.ref === currentRoute.destino) {
        fillColor = '#e74c3c';
        fillOpacity = 0.7;
        weight = 4;
      }
    }

    return {
      color: '#667eea',
      weight: weight,
      fillOpacity: fillOpacity,
      fillColor: fillColor
    };
  };

  const onEachFeature = (feature, layer) => {
    const props = feature.properties;
    
    // Store layer reference
    if (props.ref) {
      setBuildingLayers(prev => ({ ...prev, [props.ref]: layer }));
    }

    // Highlight on hover
    layer.on('mouseover', function() {
      this.setStyle({
        weight: 5,
        fillOpacity: 0.5
      });
    });

    layer.on('mouseout', function() {
      const style = getBuildingStyle(feature);
      this.setStyle(style);
    });

    // Click handler
    if (props.ref && onBuildingClick) {
      layer.on('click', function() {
        onBuildingClick(props.ref);
      });
    }
  };

  return (
    <div className="h-full w-full relative">
      <div className="absolute top-4 left-4 bg-fanshawe-brown p-3 rounded-lg shadow-lg z-[1000] border border-fanshawe-red-dark">
        <h3 className="text-sm font-bold text-fanshawe-text mb-2">Campus Map</h3>
        <p className="text-xs text-fanshawe-text opacity-70">Click on buildings for info</p>
      </div>

      {geoJsonData ? (
        <MapContainer
          center={[43.0125, -81.2002]}
          zoom={16}
          style={{ height: '100%', width: '100%' }}
          className="z-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={20}
          />
          
          <GeoJSON
            data={geoJsonData}
            style={getBuildingStyle}
            onEachFeature={onEachFeature}
          />

          {mapBounds && <FitBounds bounds={mapBounds} />}

          {currentRoute && currentRoute.path && (
            <Polyline
              positions={currentRoute.path}
              color="#3498db"
              weight={4}
              opacity={0.8}
            />
          )}
        </MapContainer>
      ) : (
        <div className="h-full w-full flex items-center justify-center bg-fanshawe-dark">
          <div className="text-fanshawe-text">Loading map...</div>
        </div>
      )}
    </div>
  );
}
