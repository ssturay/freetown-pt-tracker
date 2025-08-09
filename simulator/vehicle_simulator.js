// /simulator/vehicle_simulator.js
const fs = require("fs");
const axios = require("axios");
const path = require("path");

// Backend ping endpoint
const BACKEND_URL = "https://freetown-pt-tracker-backend.onrender.com/api/location/update";

// Load routes from GeoJSON
const routesPath = path.join(__dirname, "routes", "freetown_routes.geojson");
const geojson = JSON.parse(fs.readFileSync(routesPath));

// Public transport modes to simulate
const supportedModes = [
  "Podapoda",
  "Keke",
  "Taxi",
  "Paratransit Bus",
  "WAKA FINE Bus",
  "Motorbike"
];

// Number of simulated vehicles per route
const VEHICLES_PER_ROUTE = 3;

const vehicles = [];

supportedModes.forEach((mode) => {
  const matchingRoutes = geojson.features.filter(
    f => f.properties?.mode?.toLowerCase() === mode.toLowerCase()
  );

  matchingRoutes.forEach((routeFeature, routeIdx) => {
    const coords = routeFeature.geometry?.coordinates;

    if (coords?.length > 0) {
      for (let i = 0; i < VEHICLES_PER_ROUTE; i++) {
        const id = `${mode.toLowerCase().replace(/\s+/g, "")}_${routeIdx}_${i}`;
        const randomStart = Math.floor(Math.random() * coords.length);
        vehicles.push({
          id,
          mode,
          path: coords,
          positionIndex: randomStart
        });
      }
    }
  });
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

    vehicle.positionIndex = (vehicle.positionIndex + 1) % vehicle.path.length;
  });
}

console.log(`🚍 Simulator started for ${vehicles.length} vehicles. Pinging every 10s...`);
setInterval(updateVehicles, 10000);
