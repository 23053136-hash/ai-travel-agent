# transport_ml.py — ML model for predicting optimal transport modes in India
import numpy as np  # type: ignore
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor # type: ignore
from sklearn.neighbors import KNeighborsClassifier # type: ignore
from sklearn.preprocessing import LabelEncoder # type: ignore

class TransportModePredictor:
    def __init__(self):
        self.mode_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.price_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self._train_models()

    def _train_models(self):
        """
        Train an ML model to determine allowed transport modes.
        Features: [distance_km, budget_per_person, travel_days]
        Target Classes:
          0: Bus/Train only (Short distance < 300km, or very low budget)
          1: Train/Flight (Medium distance 300-800km)
          2: Flight mostly (Long distance > 800km)
        """
        X_train = []
        y_train = []
        
        # Generate synthetic training data representing Indian travel heuristics
        for distance in range(50, 2500, 50):
            for budget in [1500, 3000, 5000, 10000, 20000, 50000]:
                for days in [1, 2, 3, 5, 7, 10]:
                    
                    # Base cost calculation for classification logic
                    flight_p = max(1500, int(1500 + distance * 3.8))
                    can_afford_flight = (budget * 0.5) >= flight_p
                    
                    # Rule 1: If distance < 300, NEVER flight (Class 0: train, bus)
                    if distance < 300:
                        target = 0
                    
                    # Rule 2: If distance > 800
                    elif distance > 800:
                        if can_afford_flight:
                            target = 2  # Flight
                        else:
                            target = 1  # Force Train/Flight so train is allowed!
                            
                    # Rule 3: Medium distance (300-800)
                    else:
                        if can_afford_flight:
                            target = 1  # Train/Flight
                        else:
                            target = 0  # No flight, stick to train/bus
                            
                    X_train.append([distance, budget, days])
                    y_train.append(target)
        
        self.mode_model.fit(X_train, y_train)

        # Train Price Model on realistic distance-based constraints
        X_price = []
        y_price = []
        for dist in range(50, 3050, 50):
            # Price target format (Single Way): [Flight, Train, Bus]
            flight_p = max(2800, int(2800 + dist * 3.2))
            train_p = max(450, int(450 + dist * 1.4))
            bus_p = max(350, int(350 + dist * 1.0))
            X_price.append([dist])
            y_price.append([flight_p, train_p, bus_p])
        
        self.price_model.fit(X_price, y_price)

    def predict_modes(self, distance: int, budget_per_person: int, days: int) -> list[str]:
        # Force remove flight option if distance < 300 irrespective of ML uncertainty
        if distance < 300:
            return ["train", "bus"]
            
        features = np.array([[distance, budget_per_person, days]])
        prediction = self.mode_model.predict(features)[0]
        
        if prediction == 0:
            return ["train", "bus"]
        elif prediction == 1:
            return ["train", "flight"]
        else:
            return ["flight"]
            
    def predict_prices(self, distance: int) -> dict[str, int]:
        """Returns predicted [flight_price, train_price, bus_price] for 1 person."""
        prices = self.price_model.predict(np.array([[distance]]))[0]
        return {
            "flight": int(prices[0]),
            "train": int(prices[1]),
            "bus": int(prices[2])
        }

# Singleton instance
transport_ml = TransportModePredictor()

class HotelPredictor:
    def __init__(self):
        self.model = KNeighborsClassifier(n_neighbors=1)
        self.city_encoder = LabelEncoder()
        self.hotel_encoder = LabelEncoder()
        self._teach_model()

    def _teach_model(self):
        # Master dataset of Indian cities and their iconic hotels across 3 tiers (Budget, Comfort, Luxury)
        db = {
            "delhi": [("Zostel Delhi", 800), ("Radisson Blu", 4000), ("The Leela Palace", 12000)],
            "mumbai": [("Mumbai Backpacker", 1000), ("Trident Bandra", 5000), ("Taj Mahal Palace", 15000)],
            "goa": [("Hostel Crowd", 600), ("Novotel Goa", 6000), ("W Goa", 14000)],
            "bangalore": [("Loco Hostel", 900), ("Royal Orchid", 4500), ("The Ritz-Carlton", 13000)],
            "jaipur": [("Moustache Hostel", 500), ("ITC Rajputana", 5500), ("Rambagh Palace", 25000)],
            "kolkata": [("Kolkata Backpacker", 700), ("ITC Sonar", 6500), ("The Oberoi Grand", 14000)],
            "chennai": [("Zostel Chennai", 800), ("ITC Grand Chola", 7000), ("Taj Coromandel", 13000)],
            "hyderabad": [("Nomad Hostel", 600), ("Taj Krishna", 6500), ("Taj Falaknuma", 16000)],
            "varanasi": [("Moustache Varanasi", 400), ("Taj Ganges", 5000), ("BrijRama Palace", 12000)],
            "agra": [("Zostel Agra", 500), ("Courtyard Marriott", 4000), ("The Oberoi Amarvilas", 30000)],
        }
        
        cities = list(db.keys())
        cities.append("generic")
        self.city_encoder.fit(cities)
        
        X = []
        y_hotels = []
        
        # Train the ML model by simulating thousands of search queries across varying budgets
        for p in range(300, 30000, 200):
            for city, hotels in db.items():
                cid = self.city_encoder.transform([city])[0]
                best_h = hotels[0][0]
                min_diff = abs(hotels[0][1] - p)
                for h, price in hotels:
                    if abs(price - p) < min_diff:
                        best_h = h
                        min_diff = abs(price - p)
                        
                X.append([cid, p])
                y_hotels.append(best_h)
                
        # Generic fallback learning
        generic_hotels = [("City Budget Stay", 800), ("City Comfort Hotel", 4000), ("City Luxury Resort", 12000)]
        for p in range(300, 30000, 200):
            cid = self.city_encoder.transform(["generic"])[0]
            best_h = generic_hotels[0][0]
            m = abs(generic_hotels[0][1] - p)
            for h, p2 in generic_hotels:
                if abs(p2 - p) < m:
                    best_h = h
                    m = abs(p2 - p)
            X.append([cid, p])
            y_hotels.append(best_h)
            
        self.hotel_encoder.fit(y_hotels)
        y = self.hotel_encoder.transform(y_hotels)
        self.model.fit(X, y)
        
    def predict_hotel(self, city: str, budget: int) -> str:
        """Query the ML model to output the perfect top hotel fit for the input city and budget"""
        c = city.lower().strip()
        try:
            cid = self.city_encoder.transform([c])[0]
        except ValueError:
            cid = self.city_encoder.transform(["generic"])[0]
            
        pred_id = self.model.predict([[cid, budget]])[0]
        hotel_name = self.hotel_encoder.inverse_transform([pred_id])[0]
        
        if "City" in str(hotel_name):
            hotel_name = str(hotel_name).replace("City", city.capitalize())
            
        return str(hotel_name)

hotel_predictor = HotelPredictor()
