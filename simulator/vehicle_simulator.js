// /simulator/vehicle_simulator.js
const fs = require("fs");
const axios = require("axios");
const path = require("path");

// Backend ping endpoint
const BACKEND_URL = "https://freetown-pt-tracker-backend.onrender.com/api/location/update";

// Load routes from GeoJSON
const routesPath = path.join(__dirname, "routes", "freetown_routes.geojson");
const geojson = JSON.parse(fs.readFileSync(routesPath));

// Map of modes you care about
const supportedModes = [
  "Podapoda",
  "Keke",
  "Taxi",
  "Paratransit Bus",
  "WAKA FINE Bus",
  "Motorbike"
];

// One simulated vehicle per mode
const vehicles = [];

supportedModes.forEach((mode, index) => {
  // Find the first matching route for this mode
  const routeFeature = geojson.features.find(f =>
    f.properties.mode?.toLowerCase() === mode.toLowerCase()
  );

  if (routeFeature && routeFeature.geometry?.coordinates?.length > 0) {
    const coords = routeFeature.geometry.coordinates;

    vehicles.push({
      id: `${mode.toLowerCase().replace(/\s+/g, "")}_${index}`,
      mode,
      path: coords,
      positionIndex: Math.floor(Math.random() * coords.length) // start randomly
    });
  } else {
    console.warn(`⚠️ No route found for mode: ${mode}`);
  }
});

function updateVehicles() {
  vehicles.forEach(async (vehicle) => {
    const coord = vehicle.path[vehicle.positionIndex % vehicle.path.length];
    const [lon, lat] = coord;

    try {
      await axios.get(BACKEND_URL, {
        params: {
          id: vehicle.id,
          lat,
          lon,
          mode: vehicle.mode
        }
      });
      console.log(`✅ ${vehicle.id} (${vehicle.mode}) → ${lat.toFixed(5)}, ${lon.toFixed(5)}`);
    } catch (err) {
      console.error(`❌ ${vehicle.id} failed:`, err.message);
    }

    // Move to next point (looping)
    vehicle.positionIndex = (vehicle.positionIndex + 1) % vehicle.path.length;
  });
}

console.log("🚍 Simulator started. Sending pings every 10s...");
setInterval(updateVehicles, 10000);
