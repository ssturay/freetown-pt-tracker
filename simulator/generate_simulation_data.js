const fs = require("fs");

// Load your actual GeoJSON file
const routes = JSON.parse(fs.readFileSync("data/routes.geojson", "utf-8"));

const vehicles = [];

routes.features.forEach((feature, routeIndex) => {
  const mode = feature.properties?.mode || "Unknown";
  const path = feature.geometry.coordinates;

  // Simulate 2 vehicles per route
  for (let i = 0; i < 2; i++) {
    vehicles.push({
      id: `${mode.toLowerCase().replace(/\s+/g, "")}_${routeIndex}_${i + 1}`,
      mode,
      path,
      positionIndex: Math.floor(Math.random() * path.length)
    });
  }
});

// Save the simulated data
fs.writeFileSync("simulator/vehicle_data.json", JSON.stringify(vehicles, null, 2));
console.log("✅ Generated vehicle simulation data for all routes.");
