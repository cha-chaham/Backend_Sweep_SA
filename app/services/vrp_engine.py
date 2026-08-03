import math
import random
import time

class VRPEngine:
    def __init__(self, customers_db):
        random.seed(48)

        self.capacity = 50
        self.speed_kmh = 30
        self.service_time = 10
        self.max_time_minutes = 120

        # Depot tetap dipusatkan pada Depot Air Tahu Gurih
        self.depot = {
            'name': 'Depot Air Tahu Gurih',
            'lat': -0.9106327,
            'lon': 119.8624957,
            'demand': 0
        }

        # Memetakan data dari database (SQLAlchemy models) ke format node (N0, N1, N2, ...)
        self.raw_data = {'N0': self.depot}

        for idx, customer in enumerate(customers_db, start=1):
            node_key = f'N{idx}'
            self.raw_data[node_key] = {
                'name': customer.name,
                'lat': customer.lat,
                'lon': customer.lon,
                'demand': customer.demand
            }

        self.toko_data = {k: v for k, v in self.raw_data.items() if k != 'N0'}
        self.dist_matrix = self._generate_distance_matrix()
        print(self.raw_data);

    def _calculate_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def _generate_distance_matrix(self):
        matrix = {}
        nodes = list(self.raw_data.keys())
        for n1 in nodes:
            matrix[n1] = {}
            for n2 in nodes:
                if n1 == n2:
                    matrix[n1][n2] = 0.0
                else:
                    matrix[n1][n2] = self._calculate_haversine(
                        self.raw_data[n1]['lat'], self.raw_data[n1]['lon'],
                        self.raw_data[n2]['lat'], self.raw_data[n2]['lon']
                    )
        return matrix

    def _hitung_jarak_rute(self, rute):
        return sum(self.dist_matrix[rute[i]][rute[i+1]] for i in range(len(rute) - 1))

    def _hitung_estimasi_waktu(self, jarak_km, list_rute):
        waktu_jalan = (jarak_km / self.speed_kmh) * 60
        jumlah_toko_riil = sum(1 for toko in list_rute if toko != 'N0')
        waktu_layanan = jumlah_toko_riil * self.service_time
        return waktu_jalan + waktu_layanan

    def _hitung_sudut_polar(self, lat_toko, lon_toko, lat_depot, lon_depot):
        d_lon = lon_toko - lon_depot
        d_lat = lat_toko - lat_depot
        sudut = math.atan2(d_lat, d_lon)
        return math.degrees(sudut) % 360

    def _hitung_total_jarak_semua_trip(self, semua_rute):
        return sum(self._hitung_jarak_rute(rute) for rute in semua_rute)

    def _cek_validasi_constraint(self, semua_rute):
        for rute in semua_rute:
            muatan = sum(self.raw_data[node]['demand'] for node in rute if node != 'N0')
            if muatan > self.capacity:
                return False

            jarak = self._hitung_jarak_rute(rute)
            waktu = self._hitung_estimasi_waktu(jarak, rute)
            if waktu > self.max_time_minutes:
                return False
        return True

    def sweep_clustering(self):
        toko_dengan_sudut = []
        for node, data in self.toko_data.items():
            sudut = self._hitung_sudut_polar(data['lat'], data['lon'], self.depot['lat'], self.depot['lon'])
            toko_dengan_sudut.append({
                'node': node,
                'demand': data['demand'],
                'sudut': sudut
            })

        toko_urut = sorted(toko_dengan_sudut, key=lambda x: x['sudut'])

        clusters = []
        current_cluster = []
        current_load = 0

        for toko in toko_urut:
            if current_load + toko['demand'] <= self.capacity:
                current_cluster.append(toko['node'])
                current_load += toko['demand']
            else:
                clusters.append(current_cluster)
                current_cluster = [toko['node']]
                current_load = toko['demand']

        if current_cluster:
            clusters.append(current_cluster)

        return [['N0'] + cluster + ['N0'] for cluster in clusters]

    def simulated_annealing_multi_trip(self, rute_awal_sweep, T0=1000, alpha=0.99, T_final=0.001):
        current_solution = [rute[:] for rute in rute_awal_sweep]
        best_solution = [rute[:] for rute in current_solution]

        current_dist = self._hitung_total_jarak_semua_trip(current_solution)
        best_dist = current_dist

        total_toko = sum(len(rute) - 2 for rute in current_solution)
        L = total_toko * 50 if total_toko > 0 else 50
        T = T0

        while T > T_final:
            for _ in range(L):
                new_solution = [rute[:] for rute in current_solution]

                if random.random() < 0.5 and len(new_solution) > 1:
                    t1, t2 = random.sample(range(len(new_solution)), 2)
                    if len(new_solution[t1]) > 2 and len(new_solution[t2]) > 2:
                        idx1 = random.randint(1, len(new_solution[t1]) - 2)
                        idx2 = random.randint(1, len(new_solution[t2]) - 2)
                        new_solution[t1][idx1], new_solution[t2][idx2] = new_solution[t2][idx2], new_solution[t1][idx1]
                else:
                    t1 = random.randint(0, len(new_solution) - 1)
                    if len(new_solution[t1]) > 3:
                        idx1, idx2 = random.sample(range(1, len(new_solution[t1]) - 1), 2)
                        new_solution[t1][idx1], new_solution[t1][idx2] = new_solution[t1][idx2], new_solution[t1][idx1]

                if self._cek_validasi_constraint(new_solution):
                    new_dist = self._hitung_total_jarak_semua_trip(new_solution)
                    delta = new_dist - current_dist

                    if delta < 0 or random.random() < math.exp(-delta / T):
                        current_solution = [rute[:] for rute in new_solution]
                        current_dist = new_dist

                        if current_dist < best_dist:
                            best_solution = [rute[:] for rute in current_solution]
                            best_dist = current_dist

            T *= alpha

        return best_solution, best_dist

    def run_optimization(self):
        start_time = time.time()

        rute_awal_sweep = self.sweep_clustering()
        rute_optimal_sa, total_jarak_sa = self.simulated_annealing_multi_trip(rute_awal_sweep, T0=1000, alpha=0.99)

        waktu_komputasi = time.time() - start_time
        hasil_akhir = []

        for i in range(len(rute_optimal_sa)):
            rute_sa = rute_optimal_sa[i]
            jarak_sa = self._hitung_jarak_rute(rute_sa)
            waktu_sa = self._hitung_estimasi_waktu(jarak_sa, rute_sa)
            muatan_sa = sum(self.raw_data[n]['demand'] for n in rute_sa if n != 'N0')
            is_feasible = waktu_sa <= self.max_time_minutes

            # Ubah kode node (N0, N1, dst) menjadi nama toko asli
            nama_rute = [self.raw_data[node]['name'] for node in rute_sa]

            hasil_akhir.append({
                "trip_id": i + 1,
                "route": nama_rute,
                "total_demand": muatan_sa,
                "total_distance_km": round(jarak_sa, 2),
                "total_time_minutes": round(waktu_sa, 2),
                "is_feasible": is_feasible
            })

        return {
            "status": "success",
            "depot": self.depot,
            "total_trips": len(hasil_akhir),
            "total_distance_optimal_km": round(total_jarak_sa, 2),
            "computation_time_seconds": round(waktu_komputasi, 4),
            "routes": hasil_akhir
        }