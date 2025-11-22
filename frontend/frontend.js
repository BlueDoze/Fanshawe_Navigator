import React, { useState, useRef, useEffect } from 'react';
import { Send, Map, X, MessageSquare } from 'lucide-react';

export default function FanshaweNavigator() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m Fanshawe Navigator. How can I help you find your way around campus today?' }
  ]);
  const [input, setInput] = useState('');
  const [showMap, setShowMap] = useState(false);
  const [mapData, setMapData] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Sample GeoJSON data - replace with your actual GeoJSON file
  const sampleGeoJSON = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: {
          name: "Main Building",
          description: "Administration and Student Services"
        },
        geometry: {
          type: "Point",
          coordinates: [-81.1996, 43.0126]
        }
      },
      {
        type: "Feature",
        properties: {
          name: "Library",
          description: "Fanshawe College Library"
        },
        geometry: {
          type: "Point",
          coordinates: [-81.1990, 43.0130]
        }
      }
    ]
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // Simulate bot response - replace with your actual API call
    setTimeout(() => {
      const botResponse = {
        role: 'assistant',
        content: `I understand you're asking about: "${input}". Let me help you navigate to that location. Would you like me to show it on the map?`
      };
      setMessages(prev => [...prev, botResponse]);
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMap = () => {
    setShowMap(!showMap);
    if (!showMap && !mapData) {
      setMapData(sampleGeoJSON);
    }
  };

  return (
    <div className="flex h-screen bg-[#161917] text-[#e1e3db]">
      {/* Sidebar */}
      <div className="w-64 bg-[#70160e] border-r border-[#9e0004] flex flex-col">
        <div className="p-4 border-b border-[#9e0004]">
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare className="text-[#b9030f]" size={24} />
            <h1 className="text-xl font-bold text-[#e1e3db]">Fanshawe Navigator</h1>
          </div>
          <button className="w-full bg-[#b9030f] hover:bg-[#9e0004] text-[#e1e3db] py-2 px-4 rounded transition-colors">
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="text-sm text-[#e1e3db] opacity-70">
            <p className="mb-2">Recent Chats</p>
            <div className="space-y-2">
              <div className="p-2 rounded hover:bg-[#9e0004] cursor-pointer">Campus Navigation</div>
              <div className="p-2 rounded hover:bg-[#9e0004] cursor-pointer">Building Locations</div>
              <div className="p-2 rounded hover:bg-[#9e0004] cursor-pointer">Parking Information</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-[#70160e] border-b border-[#9e0004] p-4 flex justify-between items-center">
          <h2 className="text-lg font-semibold">Fanshawe Campus Assistant</h2>
          <button
            onClick={toggleMap}
            className="flex items-center gap-2 bg-[#b9030f] hover:bg-[#9e0004] px-4 py-2 rounded transition-colors"
          >
            <Map size={20} />
            {showMap ? 'Hide Map' : 'Show Map'}
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    msg.role === 'user'
                      ? 'bg-[#b9030f] text-[#e1e3db]'
                      : 'bg-[#70160e] text-[#e1e3db]'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-[#9e0004] p-4 bg-[#161917]">
          <div className="max-w-3xl mx-auto flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about campus locations, buildings, parking..."
              className="flex-1 bg-[#70160e] text-[#e1e3db] border border-[#9e0004] rounded-lg px-4 py-3 focus:outline-none focus:border-[#b9030f] placeholder-[#e1e3db] placeholder-opacity-50"
            />
            <button
              onClick={handleSend}
              className="bg-[#b9030f] hover:bg-[#9e0004] text-[#e1e3db] p-3 rounded-lg transition-colors"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Map Modal */}
      {showMap && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-[#161917] rounded-lg w-[90%] h-[90%] flex flex-col border-2 border-[#b9030f]">
            <div className="flex justify-between items-center p-4 border-b border-[#9e0004]">
              <h3 className="text-xl font-bold text-[#e1e3db]">Campus Map</h3>
              <button
                onClick={toggleMap}
                className="text-[#e1e3db] hover:text-[#b9030f] transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <div className="flex-1 p-4 overflow-auto">
              <div className="bg-[#70160e] rounded-lg p-6 h-full">
                <h4 className="text-lg mb-4 text-[#e1e3db]">Campus Locations (GeoJSON Data)</h4>
                {mapData && (
                  <div className="space-y-4">
                    {mapData.features.map((feature, idx) => (
                      <div key={idx} className="bg-[#161917] p-4 rounded border border-[#9e0004]">
                        <h5 className="font-bold text-[#b9030f] mb-2">
                          {feature.properties.name}
                        </h5>
                        <p className="text-[#e1e3db] text-sm mb-2">
                          {feature.properties.description}
                        </p>
                        <p className="text-[#e1e3db] text-xs opacity-70">
                          Coordinates: {feature.geometry.coordinates.join(', ')}
                        </p>
                      </div>
                    ))}
                    <div className="mt-6 p-4 bg-[#161917] rounded border border-[#9e0004]">
                      <p className="text-sm text-[#e1e3db] opacity-70">
                        Note: Replace the sample GeoJSON data with your actual campus map data.
                        You can integrate a mapping library like Leaflet or Mapbox for interactive maps.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}