// simulator/vehicle_simulator.js
const axios = require("axios");

// Backend endpoint for pings
const BACKEND_URL = "https://freetown-pt-tracker-backend.onrender.com/api/location/update";

// Define vehicle paths (simulate short paths)
const VEHICLES = [
  { id: "poda001", mode: "Podapoda", path: [[8.480, -13.230], [8.481, -13.231], [8.482, -13.232]] },
  { id: "keke101", mode: "Keke", path: [[8.470, -13.220], [8.471, -13.221], [8.472, -13.222]] },
  { id: "taxiX", mode: "Taxi", path: [[8.465, -13.215], [8.466, -13.216], [8.467, -13.217]] },
  { id: "para888", mode: "Paratransit Bus", path: [[8.490, -13.240], [8.491, -13.241], [8.492, -13.242]] },
  { id: "waka505", mode: "WAKA FINE Bus", path: [[8.475, -13.225], [8.476, -13.226], [8.477, -13.227]] },
  { id: "motoZX", mode: "Motorbike", path: [[8.460, -13.210], [8.461, -13.211], [8.462, -13.212]] },
];

let index = 0;

function updateVehicles() {
  VEHICLES.forEach(async (vehicle) => {
    const coord = vehicle.path[index % vehicle.path.length];
    try {
      await axios.get(BACKEND_URL, {
        params: {
          id: vehicle.id,
          lat: coord[0],
          lon: coord[1],
          mode: vehicle.mode
        }
      });
      console.log(`✅ ${vehicle.id} (${vehicle.mode}) updated to ${coord[0]}, ${coord[1]}`);
    } catch (err) {
      console.error(`❌ ${vehicle.id} failed:`, err.message);
    }
  });
  index++;
}

console.log("🚀 Simulator running for all 6 modes... updating every 10s");
setInterval(updateVehicles, 10000);
