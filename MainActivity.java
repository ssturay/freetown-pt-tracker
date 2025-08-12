package com.example.pttracker;

import android.Manifest;
import android.content.pm.PackageManager;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONObject;

import java.util.HashMap;
import java.util.Map;

public class MainActivity extends AppCompatActivity {

    private EditText vehicleIdInput;
    private Spinner modeSpinner;
    private Button startBtn, stopBtn;

    private Handler handler = new Handler();
    private boolean isTracking = false;
    private RequestQueue requestQueue;
    private android.location.LocationManager locationManager;

    private static final String BACKEND_URL = "https://freetown-pt-tracker-backend.onrender.com/api/update_vehicle";
    private static final int LOCATION_PERMISSION_REQUEST = 100;

    private Runnable sendUpdateTask = new Runnable() {
        @Override
        public void run() {
            if (isTracking) {
                sendVehicleUpdate();
                handler.postDelayed(this, 5000); // send every 5 seconds
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        vehicleIdInput = findViewById(R.id.vehicleId);
        modeSpinner = findViewById(R.id.modeSpinner);
        startBtn = findViewById(R.id.startTracking);
        stopBtn = findViewById(R.id.stopTracking);

        requestQueue = Volley.newRequestQueue(this);
        locationManager = (android.location.LocationManager) getSystemService(LOCATION_SERVICE);

        startBtn.setOnClickListener(v -> startTracking());
        stopBtn.setOnClickListener(v -> stopTracking());

        checkLocationPermission();
    }

    private void checkLocationPermission() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, LOCATION_PERMISSION_REQUEST);
        }
    }

    private void startTracking() {
        String vehicleId = vehicleIdInput.getText().toString().trim();
        String mode = modeSpinner.getSelectedItem().toString().trim().toLowerCase();

        if (vehicleId.isEmpty() || mode.isEmpty()) {
            Toast.makeText(this, "Enter Vehicle ID and Mode", Toast.LENGTH_SHORT).show();
            return;
        }

        isTracking = true;
        handler.post(sendUpdateTask);
        Toast.makeText(this, "Started tracking " + vehicleId, Toast.LENGTH_SHORT).show();
    }

    private void stopTracking() {
        isTracking = false;
        handler.removeCallbacks(sendUpdateTask);
        Toast.makeText(this, "Stopped tracking", Toast.LENGTH_SHORT).show();
    }

    private void sendVehicleUpdate() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "Location permission not granted", Toast.LENGTH_SHORT).show();
            return;
        }

        Location location = locationManager.getLastKnownLocation(android.location.LocationManager.GPS_PROVIDER);
        if (location == null) {
            Toast.makeText(this, "Waiting for GPS fix...", Toast.LENGTH_SHORT).show();
            return;
        }

        String vehicleId = vehicleIdInput.getText().toString().trim();
        String mode = modeSpinner.getSelectedItem().toString().trim().toLowerCase();

        Map<String, Object> payload = new HashMap<>();
        payload.put("id", vehicleId);
        payload.put("mode", mode);
        payload.put("lat", location.getLatitude());
        payload.put("lon", location.getLongitude());

        JSONObject jsonPayload = new JSONObject(payload);

        JsonObjectRequest request = new JsonObjectRequest(Request.Method.POST, BACKEND_URL, jsonPayload,
                response -> {
                    // Optional: show minimal feedback
                },
                error -> {
                    Toast.makeText(this, "Update failed: " + error.getMessage(), Toast.LENGTH_SHORT).show();
                });

        requestQueue.add(request);
    }
}
