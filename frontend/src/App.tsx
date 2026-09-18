import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  Gauge,
  Thermometer,
  Zap,
  RotateCw,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

import "./App.css";

interface Equipment {
  equipment_id: string;
  timestamp: string;
  temperature: number;
  vibration: number;
  load_percentage: number;
  motor_current: number;
  rpm: number;
  operating_hours: number;
  emergency_stop: boolean;
}

interface Alert {
  equipment_id: string;
  timestamp: string;
  type: string;
  severity: string;
  message: string;
  value: number | boolean;
  threshold: number | boolean;
}

interface EquipmentHealth {
  equipment_id: string;
  timestamp: string;
  status: "NORMAL" | "WARNING" | "CRITICAL" | "UNKNOWN";
  health_score: number;
  reason: string;
}

interface WebSocketMessage {
  type: string;
  data?: Equipment;
}

const API_BASE_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws";

function App() {
  const [equipmentList, setEquipmentList] =
    useState<Equipment[]>([]);

  const [fleetHealth, setFleetHealth] =
    useState<EquipmentHealth[]>([]);

  const [selectedEquipmentId, setSelectedEquipmentId] =
    useState<string>("");

  const [history, setHistory] =
    useState<Equipment[]>([]);

  const [health, setHealth] =
    useState<EquipmentHealth | null>(null);

  const [alerts, setAlerts] =
    useState<Alert[]>([]);

  const [error, setError] =
    useState<string | null>(null);

  const [webSocketConnected, setWebSocketConnected] =
    useState(false);

  const reconnectTimeoutRef =
    useRef<number | null>(null);

  /*
   * =========================================================
   * INITIAL TELEMETRY + FLEET HEALTH
   *
   * REST is used here for initial dashboard loading.
   * Live telemetry is subsequently handled by WebSocket.
   * =========================================================
   */

  useEffect(() => {
    const fetchInitialDashboardData = async () => {
      try {
        const [
          telemetryResponse,
          fleetHealthResponse,
        ] = await Promise.all([
          axios.get<Equipment[]>(
            `${API_BASE_URL}/api/telemetry/latest`
          ),

          axios.get<EquipmentHealth[]>(
            `${API_BASE_URL}/api/health/fleet`
          ),
        ]);

        const telemetry =
          telemetryResponse.data;

        const fleetHealthData =
          fleetHealthResponse.data;

        const equipmentMap = new Map<
          string,
          Equipment
        >();

        telemetry.forEach((item) => {
          const existing =
            equipmentMap.get(
              item.equipment_id
            );

          if (
            !existing ||
            new Date(item.timestamp).getTime() >
              new Date(
                existing.timestamp
              ).getTime()
          ) {
            equipmentMap.set(
              item.equipment_id,
              item
            );
          }
        });

        const latestEquipment =
          Array.from(
            equipmentMap.values()
          ).sort((a, b) =>
            a.equipment_id.localeCompare(
              b.equipment_id
            )
          );

        setEquipmentList(
          latestEquipment
        );

        setFleetHealth(
          fleetHealthData
        );

        if (
          !selectedEquipmentId &&
          latestEquipment.length > 0
        ) {
          setSelectedEquipmentId(
            latestEquipment[0]
              .equipment_id
          );
        }

        setError(null);
      } catch (requestError) {
        console.error(
          requestError
        );

        setError(
          "Unable to connect to the monitoring backend."
        );
      }
    };

    fetchInitialDashboardData();
  }, [selectedEquipmentId]);

  /*
   * =========================================================
   * MQTT → WEBSOCKET → REACT
   *
   * WebSocket is now the live telemetry channel.
   * =========================================================
   */

  useEffect(() => {
    let websocket: WebSocket | null =
      null;

    let isMounted = true;

    const connectWebSocket = () => {
      if (!isMounted) {
        return;
      }

      websocket = new WebSocket(
        WS_URL
      );

      websocket.onopen = () => {
        console.log(
          "WebSocket connected."
        );

        if (isMounted) {
          setWebSocketConnected(
            true
          );
        }
      };

      websocket.onmessage = (
        event
      ) => {
        try {
          const message =
            JSON.parse(
              event.data
            ) as WebSocketMessage;

          if (
            message.type !==
              "telemetry" ||
            !message.data
          ) {
            return;
          }

          const telemetry =
            message.data;

          /*
           * Update the latest telemetry
           * for the corresponding crane.
           */

          setEquipmentList(
            (currentEquipment) => {
              const existingIndex =
                currentEquipment.findIndex(
                  (item) =>
                    item.equipment_id ===
                    telemetry.equipment_id
                );

              if (
                existingIndex ===
                -1
              ) {
                return [
                  ...currentEquipment,
                  telemetry,
                ].sort((a, b) =>
                  a.equipment_id.localeCompare(
                    b.equipment_id
                  )
                );
              }

              const updated =
                [...currentEquipment];

              updated[
                existingIndex
              ] = telemetry;

              return updated;
            }
          );

          /*
           * Add the telemetry point
           * to the selected equipment
           * chart in real time.
           */

          setHistory(
            (currentHistory) => {
              if (
                telemetry.equipment_id !==
                selectedEquipmentId
              ) {
                return currentHistory;
              }

              const updatedHistory = [
                ...currentHistory,
                telemetry,
              ];

              /*
               * Keep the most recent
               * 100 points in memory.
               */

              return updatedHistory
                .sort(
                  (a, b) =>
                    new Date(
                      a.timestamp
                    ).getTime() -
                    new Date(
                      b.timestamp
                    ).getTime()
                )
                .slice(-100);
            }
          );
        } catch (webSocketError) {
          console.error(
            "WebSocket message error:",
            webSocketError
          );
        }
      };

      websocket.onerror = () => {
  if (isMounted) {
    setWebSocketConnected(false);
  }
};

      websocket.onclose = () => {
        console.log(
          "WebSocket disconnected."
        );

        if (isMounted) {
          setWebSocketConnected(
            false
          );

          /*
           * Reconnect automatically
           * after 2 seconds.
           */

          reconnectTimeoutRef.current =
            window.setTimeout(
              connectWebSocket,
              2000
            );
        }
      };
    };

    connectWebSocket();

    return () => {
      isMounted = false;

      if (
        reconnectTimeoutRef.current
      ) {
        window.clearTimeout(
          reconnectTimeoutRef.current
        );
      }

      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  /*
   * =========================================================
   * FLEET HEALTH
   *
   * Health remains REST-based because the backend
   * health endpoint calculates the current condition.
   * =========================================================
   */

  useEffect(() => {
    const fetchFleetHealth = async () => {
      try {
        const response =
          await axios.get<
            EquipmentHealth[]
          >(
            `${API_BASE_URL}/api/health/fleet`
          );

        setFleetHealth(
          response.data
        );
      } catch (requestError) {
        console.error(
          "Fleet health error:",
          requestError
        );
      }
    };

    fetchFleetHealth();

    const interval =
      setInterval(
        fetchFleetHealth,
        2000
      );

    return () =>
      clearInterval(interval);
  }, []);

  /*
   * =========================================================
   * SELECTED EQUIPMENT HEALTH + ALERTS
   * =========================================================
   */

  useEffect(() => {
    if (!selectedEquipmentId) {
      return;
    }

    const fetchSelectedData =
      async () => {
        try {
          const [
            alertsResponse,
            healthResponse,
          ] = await Promise.all([
            axios.get<Alert[]>(
              `${API_BASE_URL}/api/alerts`,
              {
                params: {
                  equipment_id:
                    selectedEquipmentId,
                  status: "ACTIVE",
                },
              }
            ),

            axios.get<EquipmentHealth>(
              `${API_BASE_URL}/api/health`,
              {
                params: {
                  equipment_id:
                    selectedEquipmentId,
                },
              }
            ),
          ]);

          setAlerts(
            alertsResponse.data
          );

          setHealth(
            healthResponse.data
          );
        } catch (requestError) {
          console.error(
            "Selected equipment data error:",
            requestError
          );
        }
      };

    fetchSelectedData();

    const interval =
      setInterval(
        fetchSelectedData,
        2000
      );

    return () =>
      clearInterval(interval);
  }, [selectedEquipmentId]);

  /*
   * =========================================================
   * SELECTED EQUIPMENT HISTORY
   *
   * REST provides the initial historical chart.
   * WebSocket then appends new points.
   * =========================================================
   */

  useEffect(() => {
    if (!selectedEquipmentId) {
      return;
    }

    const fetchEquipmentHistory =
      async () => {
        try {
          const response =
            await axios.get<
              Equipment[]
            >(
              `${API_BASE_URL}/api/telemetry/history`,
              {
                params: {
                  equipment_id:
                    selectedEquipmentId,
                },
              }
            );

          const selectedHistory =
            response.data.sort(
              (a, b) =>
                new Date(
                  a.timestamp
                ).getTime() -
                new Date(
                  b.timestamp
                ).getTime()
            );

          setHistory(
            selectedHistory.slice(
              -100
            )
          );
        } catch (requestError) {
          console.error(
            requestError
          );

          setHistory([]);
        }
      };

    fetchEquipmentHistory();
  }, [selectedEquipmentId]);

  /*
   * =========================================================
   * SELECTED EQUIPMENT
   * =========================================================
   */

  const equipment = useMemo(() => {
    return (
      equipmentList.find(
        (item) =>
          item.equipment_id ===
          selectedEquipmentId
      ) ?? null
    );
  }, [
    equipmentList,
    selectedEquipmentId,
  ]);

  /*
   * =========================================================
   * SELECTED ALERTS / HEALTH
   * =========================================================
   */

  const selectedAlerts =
    alerts.filter(
      (alert) =>
        alert.equipment_id ===
        selectedEquipmentId
    );

  const selectedHealth =
    health?.equipment_id ===
    selectedEquipmentId
      ? health
      : null;

  /*
   * =========================================================
   * ERROR SCREEN
   * =========================================================
   */

  if (error) {
    return (
      <div className="app">
        <div className="error-screen">
          <AlertTriangle size={48} />

          <h2>
            Backend Connection Error
          </h2>

          <p>{error}</p>

          <span>
            Make sure the FastAPI backend
            is running on port 8000.
          </span>
        </div>
      </div>
    );
  }

  /*
   * =========================================================
   * LOADING SCREEN
   * =========================================================
   */

  if (!equipment) {
    return (
      <div className="app">
        <div className="loading-screen">
          <Activity size={42} />

          <h2>
            Loading Industrial
            Monitoring System...
          </h2>

          <p>
            Connecting to equipment
            telemetry.
          </p>
        </div>
      </div>
    );
  }

  /*
   * =========================================================
   * CHART DATA
   * =========================================================
   */

  const chartData =
    history.map((item) => ({
      time: new Date(
        item.timestamp
      ).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }),

      temperature:
        item.temperature,

      vibration:
        item.vibration,

      load:
        item.load_percentage,

      motorCurrent:
        item.motor_current,

      rpm:
        item.rpm,
    }));

  const healthStatus =
    selectedHealth?.status ??
    "UNKNOWN";

  /*
   * =========================================================
   * MAIN DASHBOARD
   * =========================================================
   */

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <header className="dashboard-header">

        <div>

          <div className="brand">

            <Activity size={28} />

            <span>
              Industrial Monitor
            </span>

          </div>

          <p className="subtitle">
            Real-Time Equipment
            Monitoring Platform
          </p>

        </div>

        <div className="connection-status">

          <span
            className="status-dot"
            style={{
              background:
                webSocketConnected
                  ? "#22c55e"
                  : "#ef4444",
            }}
          ></span>

          {webSocketConnected
            ? "SYSTEM ONLINE"
            : "RECONNECTING..."}

        </div>

      </header>


      <main className="dashboard">

        {/* ===================================================
            FLEET OVERVIEW
        ==================================================== */}

        <section
          className="fleet-section"
          style={{
            marginBottom: "18px",
            padding: "24px",
            border:
              "1px solid #1e293b",
            borderRadius: "14px",
            background: "#111827",
            boxShadow:
              "0 10px 30px rgba(0, 0, 0, 0.15)",
          }}
        >

          <div className="chart-header">

            <div>

              <p className="section-label">
                FLEET OVERVIEW
              </p>

              <h2>
                Equipment Status
              </h2>

            </div>

            <span className="live-indicator">

              <span className="status-dot"></span>

              LIVE

            </span>

          </div>


          <div
            className="fleet-grid"
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(3, 1fr)",
              gap: "14px",
            }}
          >

            {equipmentList.map(
              (item) => {

                const isSelected =
                  item.equipment_id ===
                  selectedEquipmentId;

                const equipmentHealth =
                  fleetHealth.find(
                    (healthItem) =>
                      healthItem.equipment_id ===
                      item.equipment_id
                  );

                const fleetStatus =
                  equipmentHealth?.status ??
                  "UNKNOWN";

                const fleetScore =
                  equipmentHealth?.health_score ??
                  0;

                const healthColor =
                  getHealthColor(
                    fleetStatus
                  );

                const cardBorder =
                  isSelected
                    ? `1px solid ${healthColor}`
                    : `1px solid ${
                        fleetStatus ===
                        "CRITICAL"
                          ? "#991b1b"
                          : fleetStatus ===
                            "WARNING"
                          ? "#854d0e"
                          : "#1e293b"
                      }`;

                return (

                  <div
                    key={
                      item.equipment_id
                    }
                    onClick={() =>
                      setSelectedEquipmentId(
                        item.equipment_id
                      )
                    }
                    style={{
                      padding: "18px",
                      border:
                        cardBorder,
                      borderRadius:
                        "12px",
                      background:
                        "#0f172a",
                      cursor:
                        "pointer",
                      transition:
                        "border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease",
                      boxShadow:
                        isSelected
                          ? `0 0 0 1px ${healthColor}22`
                          : "none",
                    }}
                  >

                    <div
                      style={{
                        display:
                          "flex",
                        alignItems:
                          "center",
                        justifyContent:
                          "space-between",
                        gap: "10px",
                        marginBottom:
                          "16px",
                      }}
                    >

                      <strong
                        style={{
                          color:
                            "#f8fafc",
                          fontSize:
                            "16px",
                        }}
                      >
                        {
                          item.equipment_id
                        }
                      </strong>

                      <span
                        style={{
                          display:
                            "flex",
                          alignItems:
                            "center",
                          gap: "6px",
                          color:
                            healthColor,
                          fontSize:
                            "9px",
                          fontWeight:
                            700,
                          letterSpacing:
                            "0.6px",
                        }}
                      >

                        <span
                          style={{
                            width:
                              "7px",
                            height:
                              "7px",
                            borderRadius:
                              "50%",
                            background:
                              healthColor,
                            display:
                              "inline-block",
                            boxShadow:
                              `0 0 8px ${healthColor}66`,
                          }}
                        />

                        {fleetStatus}

                      </span>

                    </div>


                    <div
                      style={{
                        display:
                          "flex",
                        alignItems:
                          "baseline",
                        gap: "5px",
                        marginBottom:
                          "18px",
                      }}
                    >

                      <strong
                        style={{
                          color:
                            "#f8fafc",
                          fontSize:
                            "28px",
                          fontWeight:
                            800,
                        }}
                      >
                        {fleetScore}
                      </strong>

                      <span
                        style={{
                          color:
                            "#64748b",
                          fontSize:
                            "12px",
                          fontWeight:
                            600,
                        }}
                      >
                        /100 Health
                      </span>

                    </div>


                    <div
                      style={{
                        width:
                          "100%",
                        height:
                          "5px",
                        borderRadius:
                          "999px",
                        background:
                          "#1e293b",
                        overflow:
                          "hidden",
                        marginBottom:
                          "18px",
                      }}
                    >

                      <div
                        style={{
                          width: `${Math.max(
                            0,
                            Math.min(
                              fleetScore,
                              100
                            )
                          )}%`,
                          height:
                            "100%",
                          borderRadius:
                            "999px",
                          background:
                            healthColor,
                          transition:
                            "width 0.4s ease, background 0.2s ease",
                        }}
                      />

                    </div>


                    <div
                      style={{
                        display:
                          "grid",
                        gridTemplateColumns:
                          "repeat(2, 1fr)",
                        gap: "12px",
                      }}
                    >

                      <FleetMetric
                        label="Temperature"
                        value={`${item.temperature} °C`}
                      />

                      <FleetMetric
                        label="Load"
                        value={`${item.load_percentage}%`}
                      />

                      <FleetMetric
                        label="Motor Current"
                        value={`${item.motor_current} A`}
                      />

                      <FleetMetric
                        label="RPM"
                        value={`${item.rpm}`}
                      />

                    </div>


                    <div
                      style={{
                        marginTop:
                          "16px",
                        paddingTop:
                          "12px",
                        borderTop:
                          "1px solid #1e293b",
                        display:
                          "flex",
                        alignItems:
                          "center",
                        gap: "8px",
                        color:
                          healthColor,
                        fontSize:
                          "11px",
                        fontWeight:
                          600,
                        lineHeight:
                          "1.5",
                      }}
                    >

                      <span
                        style={{
                          width:
                            "7px",
                          height:
                            "7px",
                          borderRadius:
                            "50%",
                          background:
                            healthColor,
                          display:
                            "inline-block",
                          flexShrink:
                            0,
                        }}
                      />

                      <span>

                        {fleetStatus ===
                        "NORMAL"
                          ? "Operating normally"
                          : equipmentHealth?.reason ??
                            "Health information unavailable."}

                      </span>

                    </div>

                  </div>
                );
              }
            )}

          </div>

        </section>


        {/* ===================================================
            SELECTED EQUIPMENT
        ==================================================== */}

        <section className="equipment-header">

          <div>

            <p className="section-label">
              SELECTED EQUIPMENT
            </p>

            <div
              style={{
                display:
                  "flex",
                alignItems:
                  "center",
                gap: "14px",
                marginTop:
                  "4px",
              }}
            >

              <select
                value={
                  selectedEquipmentId
                }
                onChange={(event) =>
                  setSelectedEquipmentId(
                    event.target.value
                  )
                }
                style={{
                  padding:
                    "10px 14px",
                  borderRadius:
                    "8px",
                  border:
                    "1px solid #334155",
                  background:
                    "#0f172a",
                  color:
                    "#f8fafc",
                  fontSize:
                    "18px",
                  fontWeight:
                    700,
                  cursor:
                    "pointer",
                  outline:
                    "none",
                }}
              >

                {equipmentList.map(
                  (item) => (
                    <option
                      key={
                        item.equipment_id
                      }
                      value={
                        item.equipment_id
                      }
                    >
                      {
                        item.equipment_id
                      }
                    </option>
                  )
                )}

              </select>

            </div>

          </div>


          <div className="equipment-status">

            <span className="status-dot"></span>

            {equipment.emergency_stop
              ? "EMERGENCY STOP"
              : "RUNNING"}

          </div>

        </section>


        {/* ===================================================
            METRICS
        ==================================================== */}

        <section className="metrics-grid">

          <MetricCard
            title="Temperature"
            value={
              equipment.temperature
            }
            unit="°C"
            icon={
              <Thermometer
                size={24}
              />
            }
          />

          <MetricCard
            title="Vibration"
            value={
              equipment.vibration
            }
            unit="mm/s"
            icon={
              <Activity
                size={24}
              />
            }
          />

          <MetricCard
            title="Load"
            value={
              equipment.load_percentage
            }
            unit="%"
            icon={
              <Gauge
                size={24}
              />
            }
          />

          <MetricCard
            title="Motor Current"
            value={
              equipment.motor_current
            }
            unit="A"
            icon={
              <Zap
                size={24}
              />
            }
          />

          <MetricCard
            title="Motor Speed"
            value={
              equipment.rpm
            }
            unit="RPM"
            icon={
              <RotateCw
                size={24}
              />
            }
          />

          <MetricCard
            title="Operating Hours"
            value={
              equipment.operating_hours
            }
            unit="h"
            icon={
              <Activity
                size={24}
              />
            }
          />

        </section>


        {/* ===================================================
            EQUIPMENT HEALTH
        ==================================================== */}

        <section className="health-section">

          <div className="health-header">

            <div>

              <p className="section-label">
                EQUIPMENT HEALTH
              </p>

              <h2>
                Overall Equipment
                Condition
              </h2>

            </div>

            <div
              className={`health-status ${healthStatus.toLowerCase()}`}
            >

              <span className="status-dot"></span>

              {healthStatus}

            </div>

          </div>


          <div className="health-content">

            <div className="health-score-container">

              <div className="health-score">

                {
                  selectedHealth?.health_score ??
                  0
                }

                <small>
                  /100
                </small>

              </div>

              <span>
                Health Score
              </span>

            </div>


            <div className="health-details">

              <span>
                Current assessment
              </span>

              <strong>
                {
                  selectedHealth?.reason ??
                  "Health information unavailable."
                }
              </strong>

              <p>

                Last evaluated:{" "}

                {selectedHealth?.timestamp
                  ? new Date(
                      selectedHealth.timestamp
                    ).toLocaleString()
                  : "N/A"}

              </p>

            </div>

          </div>

        </section>


        {/* ===================================================
            ALERTS
        ==================================================== */}

        <section className="alerts-section">

          <div className="chart-header">

            <div>

              <p className="section-label">
                SYSTEM EVENTS
              </p>

              <h2>
                Active Alerts
              </h2>

            </div>

            <div className="alert-count">

              {
                selectedAlerts.length
              }{" "}

              {
                selectedAlerts.length ===
                1
                  ? "ALERT"
                  : "ALERTS"
              }

            </div>

          </div>


          {selectedAlerts.length ===
          0 ? (

            <div className="no-alerts">

              <span className="status-dot"></span>

              <div>

                <strong>
                  No Active Alerts
                </strong>

                <p>
                  Equipment is operating
                  within configured
                  thresholds.
                </p>

              </div>

            </div>

          ) : (

            <div className="alerts-list">

              {selectedAlerts.map(
                (alert, index) => (

                  <div
                    className={`alert-item ${
                      alert.severity ===
                      "CRITICAL"
                        ? "critical-alert"
                        : "warning-alert"
                    }`}
                    key={`${alert.type}-${index}`}
                  >

                    <AlertTriangle
                      size={22}
                    />

                    <div className="alert-content">

                      <strong>
                        {
                          alert.type.replaceAll(
                            "_",
                            " "
                          )
                        }
                      </strong>

                      <span>
                        {
                          alert.message
                        }
                      </span>

                    </div>

                    <span className="alert-severity">
                      {
                        alert.severity
                      }
                    </span>

                  </div>

                )
              )}

            </div>

          )}

        </section>


        {/* ===================================================
            TEMPERATURE / VIBRATION
        ==================================================== */}

        <section className="chart-section">

          <div className="chart-header">

            <div>

              <p className="section-label">
                LIVE TELEMETRY
              </p>

              <h2>
                Temperature &
                Vibration
              </h2>

            </div>

            <span className="live-indicator">

              <span className="status-dot"></span>

              LIVE

            </span>

          </div>


          <div className="chart-container">

            <ResponsiveContainer
              width="100%"
              height={360}
            >

              <LineChart
                data={chartData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="time"
                />

                <YAxis />

                <Tooltip />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="temperature"
                  name="Temperature °C"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  dot={false}
                />

                <Line
                  type="monotone"
                  dataKey="vibration"
                  name="Vibration mm/s"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={false}
                />

              </LineChart>

            </ResponsiveContainer>

          </div>

        </section>


        {/* ===================================================
            LOAD / MOTOR CURRENT
        ==================================================== */}

        <section className="chart-section">

          <div className="chart-header">

            <div>

              <p className="section-label">
                EQUIPMENT LOAD
              </p>

              <h2>
                Load &
                Motor Current
              </h2>

            </div>

            <span className="live-indicator">

              <span className="status-dot"></span>

              LIVE

            </span>

          </div>


          <div className="chart-container">

            <ResponsiveContainer
              width="100%"
              height={360}
            >

              <LineChart
                data={chartData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="time"
                />

                <YAxis />

                <Tooltip />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="load"
                  name="Load %"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={false}
                />

                <Line
                  type="monotone"
                  dataKey="motorCurrent"
                  name="Motor Current A"
                  stroke="#a78bfa"
                  strokeWidth={2}
                  dot={false}
                />

              </LineChart>

            </ResponsiveContainer>

          </div>

        </section>


        {/* ===================================================
            MOTOR SPEED
        ==================================================== */}

        <section className="chart-section">

          <div className="chart-header">

            <div>

              <p className="section-label">
                MOTOR PERFORMANCE
              </p>

              <h2>
                Motor Speed
              </h2>

            </div>

            <span className="live-indicator">

              <span className="status-dot"></span>

              LIVE

            </span>

          </div>


          <div className="chart-container">

            <ResponsiveContainer
              width="100%"
              height={360}
            >

              <LineChart
                data={chartData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="time"
                />

                <YAxis />

                <Tooltip />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="rpm"
                  name="Motor Speed RPM"
                  stroke="#eab308"
                  strokeWidth={2}
                  dot={false}
                />

              </LineChart>

            </ResponsiveContainer>

          </div>

        </section>


        {/* ===================================================
            TELEMETRY INFORMATION
        ==================================================== */}

        <section className="telemetry-info">

          <div>

            <span>
              Last telemetry received
            </span>

            <strong>
              {new Date(
                equipment.timestamp
              ).toLocaleString()}
            </strong>

          </div>


          <div>

            <span>
              Emergency Stop
            </span>

            <strong>
              {equipment.emergency_stop
                ? "ACTIVE"
                : "INACTIVE"}
            </strong>

          </div>

        </section>

      </main>

    </div>
  );
}


/* =========================================================
   HEALTH COLOR
========================================================= */

function getHealthColor(
  status: EquipmentHealth["status"]
) {
  switch (status) {
    case "NORMAL":
      return "#86efac";

    case "WARNING":
      return "#fde68a";

    case "CRITICAL":
      return "#fca5a5";

    default:
      return "#94a3b8";
  }
}


/* =========================================================
   METRIC CARD
========================================================= */

interface MetricCardProps {
  title: string;
  value: number;
  unit: string;
  icon: React.ReactNode;
}

function MetricCard({
  title,
  value,
  unit,
  icon,
}: MetricCardProps) {

  return (

    <div className="metric-card">

      <div className="metric-icon">
        {icon}
      </div>

      <div className="metric-content">

        <span className="metric-title">
          {title}
        </span>

        <div className="metric-value">

          {value}

          <small>
            {unit}
          </small>

        </div>

      </div>

    </div>

  );
}


/* =========================================================
   FLEET METRIC
========================================================= */

interface FleetMetricProps {
  label: string;
  value: string;
}

function FleetMetric({
  label,
  value,
}: FleetMetricProps) {

  return (

    <div
      style={{
        display:
          "flex",
        flexDirection:
          "column",
        gap: "4px",
      }}
    >

      <span
        style={{
          color:
            "#64748b",
          fontSize:
            "10px",
          fontWeight:
            600,
          textTransform:
            "uppercase",
          letterSpacing:
            "0.6px",
        }}
      >
        {label}
      </span>

      <strong
        style={{
          color:
            "#cbd5e1",
          fontSize:
            "14px",
        }}
      >
        {value}
      </strong>

    </div>

  );
}


export default App;