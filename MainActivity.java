package com.example.freetownptdriver; // <-- update to your package

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.location.Location;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationServices;

import org.jetbrains.annotations.NotNull;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.FormBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * Simple driver-side activity:
 * - requests location permissions
 * - when tracking, posts lat/lon + id + mode to backend every 5 seconds
 * - remembers vehicle ID and last selected mode if the checkbox is checked
 *
 * NOTE: adjust BACKEND_URL to your deployed backend.
 */
public class MainActivity extends AppCompatActivity {

    private static final String PREFS = "pt_driver_prefs";
    private static final String PREF_VEHICLE_ID = "vehicle_id";
    private static final String PREF_MODE = "vehicle_mode";
    private static final String BACKEND_URL = "https://freetown-pt-tracker-backend.onrender.com/api/location/update";

    private EditText etVehicleId;
    private CheckBox cbRemember;
    private Spinner spinnerMode;
    private Button btnStart, btnStop;
    private TextView tvStatus, tvLastSent;

    private FusedLocationProviderClient fusedLocationClient;
    private Handler handler;
    private Runnable sendRunnable;
    private OkHttpClient httpClient;

    private boolean isTracking = false;
    private SharedPreferences prefs;

    // 5 seconds interval
    private static final long INTERVAL_MS = 5000L;

    // Permission launcher (modern API)
    private ActivityResultLauncher<String> requestPermissionLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main); // ensure correct layout name

        etVehicleId = findViewById(R.id.etVehicleId);
        cbRemember = findViewById(R.id.cbRememberId);
        spinnerMode = findViewById(R.id.spinnerMode);
        btnStart = findViewById(R.id.btnStart);
        btnStop = findViewById(R.id.btnStop);
        tvStatus = findViewById(R.id.tvStatus);
        tvLastSent = findViewById(R.id.tvLastSent);

        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);

        // Fuse location client
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this);

        // OkHttp client
        httpClient = new OkHttpClient.Builder()
                .callTimeout(10, TimeUnit.SECONDS)
                .build();

        // Handler for periodic sends
        handler = new Handler(Looper.getMainLooper());

        setupSpinner();
        loadSavedPreferences();
        setupPermissionLauncher();
        setupButtons();
    }

    private void setupSpinner() {
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(this,
                R.array.transport_modes, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerMode.setAdapter(adapter);
    }

    private void loadSavedPreferences() {
        String savedId = prefs.getString(PREF_VEHICLE_ID, "");
        String savedMode = prefs.getString(PREF_MODE, "");

        if (!savedId.isEmpty()) {
            etVehicleId.setText(savedId);
            cbRemember.setChecked(true);
        }

        if (!savedMode.isEmpty()) {
            ArrayAdapter<CharSequence> adapter = (ArrayAdapter<CharSequence>) spinnerMode.getAdapter();
            int pos = adapter.getPosition(savedMode);
            if (pos >= 0) spinnerMode.setSelection(pos);
        }
    }

    private void setupPermissionLauncher() {
        requestPermissionLauncher = registerForActivityResult(new ActivityResultContracts.RequestPermission(),
                new ActivityResultCallback<Boolean>() {
                    @Override
                    public void onActivityResult(Boolean isGranted) {
                        if (!isGranted) {
                            Toast.makeText(MainActivity.this, "Location permission is required to track location.", Toast.LENGTH_LONG).show();
                        }
                    }
                });
    }

    private void setupButtons() {
        btnStart.setOnClickListener(v -> {
            // Request permission if not granted
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                    != PackageManager.PERMISSION_GRANTED) {
                requestPermissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION);
                return;
            }
            String id = etVehicleId.getText().toString().trim();
            String mode = spinnerMode.getSelectedItem() != null ? spinnerMode.getSelectedItem().toString() : "";
            if (id.isEmpty() || mode.isEmpty()) {
                Toast.makeText(this, "Please enter vehicle id and select mode", Toast.LENGTH_SHORT).show();
                return;
            }
            if (cbRemember.isChecked()) {
                prefs.edit().putString(PREF_VEHICLE_ID, id).apply();
                prefs.edit().putString(PREF_MODE, mode).apply();
            } else {
                prefs.edit().remove(PREF_VEHICLE_ID).apply();
                prefs.edit().remove(PREF_MODE).apply();
            }
            startTracking(id, mode);
        });

        btnStop.setOnClickListener(v -> stopTracking());
    }

    private void startTracking(String vehicleId, String mode) {
        if (isTracking) return;
        isTracking = true;
        tvStatus.setText("Tracking: " + vehicleId + " (" + mode + ")");
        btnStart.setEnabled(false);
        btnStop.setEnabled(true);

        // create runnable to send location every INTERVAL_MS
        sendRunnable = new Runnable() {
            @Override
            public void run() {
                sendCurrentLocation(vehicleId, mode);
                if (isTracking) handler.postDelayed(this, INTERVAL_MS);
            }
        };

        // trigger first run immediately
        handler.post(sendRunnable);
    }

    private void stopTracking() {
        if (!isTracking) return;
        isTracking = false;
        handler.removeCallbacks(sendRunnable);
        tvStatus.setText("Not tracking");
        btnStart.setEnabled(true);
        btnStop.setEnabled(false);
    }

    private void sendCurrentLocation(String vehicleId, String mode) {
        // Acquire last known location and send it
        try {
            fusedLocationClient.getLastLocation()
                    .addOnSuccessListener(location -> {
                        if (location != null) {
                            postLocation(vehicleId, mode, location);
                        } else {
                            // If null, request a single update could be implemented (left simple for brevity)
                            tvLastSent.setText("Last sent: waiting for GPS fix...");
                        }
                    })
                    .addOnFailureListener(e -> {
                        tvLastSent.setText("Last sent: failed to get location");
                    });
        } catch (SecurityException e) {
            tvLastSent.setText("Last sent: permission denied");
            e.printStackTrace();
        }
    }

    private void postLocation(String vehicleId, String mode, Location location) {
        // Build POST body (GET was used in your web examples, but prefer POST from app)
        RequestBody formBody = new FormBody.Builder()
                .add("id", vehicleId)
                .add("lat", String.valueOf(location.getLatitude()))
                .add("lon", String.valueOf(location.getLongitude()))
                .add("mode", mode)
                .build();

        Request request = new Request.Builder()
                .url(BACKEND_URL)
                .post(formBody)
                .build();

        httpClient.newCall(request).enqueue(new Callback() {
            @Override public void onFailure(@NotNull Call call, @NotNull IOException e) {
                runOnUiThread(() -> tvLastSent.setText("Last sent: failed (" + e.getMessage() + ")"));
            }
            @Override public void onResponse(@NotNull Call call, @NotNull Response response) throws IOException {
                final String body = response.body() != null ? response.body().string() : "ok";
                runOnUiThread(() -> tvLastSent.setText("Last sent: " + System.currentTimeMillis() / 1000L + " — " + body));
                response.close();
            }
        });
    }

    @Override
    protected void onPause() {
        super.onPause();
        // optionally continue tracking in background if you implement a foreground service.
        // For now, we stop tracking on pause to be conservative.
        // If you want continuous background tracking, convert to a Foreground Service.
        // stopTracking();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        stopTracking();
    }

    // Optional: handle permission result to start tracking after granting permission (omitted for brevity)
}
