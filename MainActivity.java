package com.example.gpstracker;

import android.Manifest;
import android.content.pm.PackageManager;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import com.android.volley.Request;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;
import com.google.android.gms.location.*;

public class MainActivity extends AppCompatActivity {
    private FusedLocationProviderClient fusedLocationClient;
    private TextView statusText;
    private final String VEHICLE_ID = "Poda001";
    private final String SERVER_URL = "https://freetown-pt-tracker-backend.onrender.com/api/location/update";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        statusText = findViewById(R.id.statusText);

        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this);
        requestLocationUpdates();
    }

    private void requestLocationUpdates() {
        LocationRequest request = LocationRequest.create();
        request.setInterval(10000);
        request.setPriority(Priority.PRIORITY_HIGH_ACCURACY);

        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, 1);
            return;
        }

        fusedLocationClient.requestLocationUpdates(request, new LocationCallback() {
            @Override
            public void onLocationResult(@NonNull LocationResult result) {
                Location loc = result.getLastLocation();
                if (loc != null) {
                    double lat = loc.getLatitude();
                    double lon = loc.getLongitude();
                    statusText.setText("Sending: " + lat + ", " + lon);
                    sendLocationToServer(lat, lon);
                }
            }
        }, new Handler().getLooper());
    }

    private void sendLocationToServer(double lat, double lon) {
        String url = SERVER_URL + "?id=" + VEHICLE_ID + "&lat=" + lat + "&lon=" + lon;

        StringRequest req = new StringRequest(Request.Method.GET, url,
                response -> Log.d("GPS", "Sent: " + response),
                error -> Log.e("GPS", "Failed to send location", error));
        Volley.newRequestQueue(this).add(req);
    }
}
