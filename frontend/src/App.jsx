import React, { useState, useRef, useEffect } from 'react';
import { Send, Map as MapIcon, X, MessageSquare, Loader2 } from 'lucide-react';
import { MapContainer, TileLayer, GeoJSON, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Component to fit map bounds when data loads
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

export default function FanshaweNavigator() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m Fanshawe Navigator. How can I help you find your way around campus today?' }
  ]);
  const [input, setInput] = useState('');
  const [showMap, setShowMap] = useState(false);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [mapBounds, setMapBounds] = useState(null);
  const [loading, setLoading] = useState(false);
  const [routeData, setRouteData] = useState(null);
  const [originBuilding, setOriginBuilding] = useState(null);
  const [destBuilding, setDestBuilding] = useState(null);
  const messagesEndRef = useRef(null);

  const API_URL = 'http://localhost:8000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load GeoJSON data when map opens
  useEffect(() => {
    if (showMap && !geoJsonData) {
      loadGeoJSON();
    }
  }, [showMap]);

  const loadGeoJSON = async () => {
    try {
      const response = await fetch(`${API_URL}/api/geojson`);
      const data = await response.json();
      setGeoJsonData(data);
      
      // Calculate bounds
      if (data.features && data.features.length > 0) {
        const coordinates = data.features
          .filter(f => f.geometry && f.geometry.coordinates)
          .map(f => {
            if (f.geometry.type === 'Point') {
              return [[f.geometry.coordinates[1], f.geometry.coordinates[0]]];
            } else if (f.geometry.type === 'Polygon') {
              return f.geometry.coordinates[0].map(c => [c[1], c[0]]);
            }
            return [];
          })
          .flat();
        
        if (coordinates.length > 0) {
          const lats = coordinates.map(c => c[0]);
          const lngs = coordinates.map(c => c[1]);
          setMapBounds([
            [Math.min(...lats), Math.min(...lngs)],
            [Math.max(...lats), Math.max(...lngs)]
          ]);
        }
      }
    } catch (error) {
      console.error('Error loading GeoJSON:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    const userInput = input;
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mensagem: userInput })
      });

      const data = await response.json();
      
      // Add bot response
      const botResponse = {
        role: 'assistant',
        content: data.resposta || 'Sorry, I couldn\'t process that request.'
      };
      setMessages(prev => [...prev, botResponse]);

      // If there's route data, handle it
      if (data.tipo === 'navegacao' && data.origem && data.destino) {
        try {
          const routeResponse = await fetch(`${API_URL}/api/calcular-rota`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              origem: data.origem,
              destino: data.destino
            })
          });
          const routeResult = await routeResponse.json();
          setRouteData(routeResult);
          
          // Automatically open map when route is calculated
          if (!showMap) {
            setShowMap(true);
          }
        } catch (error) {
          console.error('Error calculating route:', error);
        }
      }

      // If asking about building info, optionally show map
      if (data.tipo === 'info_predio') {
        // Could auto-open map here if desired
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorResponse = {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.'
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMap = () => {
    setShowMap(!showMap);
  };

  // Style for GeoJSON features
  const getFeatureStyle = (feature) => {
    const isCollege = feature.properties.name?.includes('Fanshawe') || 
                     feature.properties.amenity === 'college';
    
    // Check if this is part of a route
    let fillColor = isCollege ? '#764ba2' : '#bdc3c7';
    let fillOpacity = isCollege ? 0.3 : 0.1;
    
    if (routeData && feature.properties.ref) {
      if (feature.properties.ref === routeData.origem) {
        fillColor = '#27ae60'; // Green for origin
        fillOpacity = 0.7;
      } else if (feature.properties.ref === routeData.destino) {
        fillColor = '#e74c3c'; // Red for destination
        fillOpacity = 0.7;
      }
    }

    return {
      color: isCollege ? '#667eea' : '#95a5a6',
      weight: isCollege ? 3 : 2,
      fillOpacity: fillOpacity,
      fillColor: fillColor
    };
  };

  // Handle feature click
  const onEachFeature = (feature, layer) => {
    if (feature.properties) {
      const props = feature.properties;
      const nome = props.name || props.nome || 'Building';
      const ref = props.ref ? ` (${props.ref})` : '';
      
      layer.on('click', async () => {
        if (props.ref) {
          try {
            const response = await fetch(`${API_URL}/api/predios/${props.ref}/info`);
            const data = await response.json();
            
            if (data.texto_formatado) {
              const infoMessage = {
                role: 'assistant',
                content: data.texto_formatado
              };
              setMessages(prev => [...prev, infoMessage]);
            }
          } catch (error) {
            console.error('Error fetching building info:', error);
          }
        }
      });

      // Hover effects
      layer.on('mouseover', function() {
        this.setStyle({
          weight: 5,
          fillOpacity: 0.5
        });
      });

      layer.on('mouseout', function() {
        this.setStyle(getFeatureStyle(feature));
      });
    }
  };

  return (
    <div className="flex h-screen bg-fanshawe-cream text-gray-800">
      {/* Sidebar */}
      <div className="w-64 bg-[#d4d6ce] border-r border-gray-300 flex flex-col">
        <div className="p-4 border-b border-gray-300">
          <div className="flex items-center justify-center mb-4">
            <img 
              src="/Fanshawe_Icons/Pressbooks_Icon_Fanshawe-NorthStar_Red-removebg-preview.png" 
              alt="Fanshawe Logo" 
              className="w-12 h-12"
            />
          </div>
          <button 
            onClick={() => {
              setMessages([
                { role: 'assistant', content: 'Hello! I\'m Fanshawe Navigator. How can I help you find your way around campus today?' }
              ]);
              setRouteData(null);
            }}
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded transition-colors"
          >
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="text-sm text-gray-600">
            <p className="mb-2 font-semibold">Quick Actions</p>
            <div className="space-y-2">
              <button 
                onClick={() => setInput("How do I get from building A to building B?")}
                className="w-full text-left p-2 rounded hover:bg-gray-200 cursor-pointer transition-colors"
              >
                Campus Navigation
              </button>
              <button 
                onClick={() => setInput("What's in building A?")}
                className="w-full text-left p-2 rounded hover:bg-gray-200 cursor-pointer transition-colors"
              >
                Building Information
              </button>
              <button
                onClick={toggleMap}
                className="w-full flex items-center justify-center gap-2 bg-fanshawe-red hover:bg-fanshawe-red-dark px-4 py-2 rounded transition-colors text-white mt-2"
              >
                <MapIcon size={20} />
                {showMap ? 'Hide Map' : 'Show Map'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-fanshawe-cream relative">
          {/* Watermark background */}
          <div 
            className="absolute inset-0 flex items-center justify-center pointer-events-none"
            style={{
              backgroundImage: 'url(/Fanshawe_Icons/Fanshawe-removebg-preview.png)',
              backgroundPosition: 'center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '50%',
              opacity: 0.05
            }}
          />
          <div className="max-w-3xl mx-auto space-y-6 relative z-10">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 shadow-md ${
                    msg.role === 'user'
                      ? 'bg-fanshawe-red text-white border border-fanshawe-red-dark'
                      : 'bg-white text-gray-800 border border-gray-300'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 border border-gray-300 rounded-lg p-4 shadow-md flex items-center gap-3">
                  <img 
                    src="/Fanshawe_Icons/Pressbooks_Icon_Fanshawe-NorthStar_Red-removebg-preview.png" 
                    alt="Loading" 
                    className="w-6 h-6 animate-spin"
                  />
                  <p className="text-gray-600 font-semibold">Thinking...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-300 p-4 bg-fanshawe-cream">
          <div className="max-w-3xl mx-auto flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              placeholder="Ask about campus locations, buildings, directions..."
              className="flex-1 bg-white text-gray-800 border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:border-fanshawe-red placeholder-gray-500"
            />
            <button
              onClick={handleSend}
              disabled={loading}
              className="bg-fanshawe-red hover:bg-fanshawe-red-dark text-white p-3 rounded-lg transition-colors disabled:opacity-50"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Map Modal */}
      {showMap && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-fanshawe-cream rounded-lg w-[90%] h-[90%] flex flex-col border-2 border-gray-400">
            <div className="flex justify-between items-center p-4 border-b border-gray-300">
              <h3 className="text-xl font-bold text-gray-800">Campus Map</h3>
              <button
                onClick={toggleMap}
                className="text-gray-800 hover:text-gray-600 transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
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
                  />
                  <GeoJSON 
                    data={geoJsonData} 
                    style={getFeatureStyle}
                    onEachFeature={onEachFeature}
                  />
                  {mapBounds && <FitBounds bounds={mapBounds} />}
                </MapContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-fanshawe-cream">Loading map...</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
