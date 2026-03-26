import http from 'k6/http';
import { check } from 'k6';

// ─────────────────────────────────────────────
//  Configuration de la charge
// ─────────────────────────────────────────────
export const options = {
  vus: 100,             // CONCURRENCY: 300 utilisateurs simultanés
  iterations: 100_000,   // NB_REQUESTS: 100 000 requêtes au total
};

// Localities réelles du dataset NY Housing
const LOCALITIES = [
  "Bronx County",
  "Brooklyn",
  "Flatbush",
  "Kings County",
  "New York",
  "New York County",
  "Queens",
  "Queens County",
  "Richmond County",
  "The Bronx",
  "United States",
];

const BASE_URL = __ENV.BASE_URL || "http://localhost:5000/houses";

export default function () {
  // Choix aléatoire d'une localité
  const locality = LOCALITIES[Math.floor(Math.random() * LOCALITIES.length)];
  
  // Construction de l'URL avec encodage des espaces (ex: "New York" -> "New%20York")
  const url = `${BASE_URL}?locality=${encodeURIComponent(locality)}&limit=20`;

  // Configuration de la requête (ajout du timeout de 10s comme dans ton Python)
  const params = {
    timeout: '10s', 
  };

  // Envoi de la requête HTTP GET
  const res = http.get(url, params);

  // Vérification que le statut est bien 200 (compte pour les "succès" vs "erreurs")
  check(res, {
    'status was 200': (r) => r.status === 200,
  });
}