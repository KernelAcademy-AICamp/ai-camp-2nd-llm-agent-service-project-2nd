/**
 * Kakao Maps Utility
 * 003-role-based-ui Feature - US5
 *
 * Utility functions for Kakao Maps integration.
 * Used by GPSTracker component for detective field work.
 */

// Kakao Maps types
interface KakaoMapOptions {
  center: { lat: number; lng: number };
  level?: number;
}

interface KakaoMarkerOptions {
  position: { lat: number; lng: number };
  title?: string;
}

// Global kakao object type
declare global {
  interface Window {
    kakao?: {
      maps: {
        load: (callback: () => void) => void;
        Map: new (
          container: HTMLElement,
          options: { center: unknown; level: number }
        ) => KakaoMap;
        LatLng: new (lat: number, lng: number) => KakaoLatLng;
        Marker: new (options: { map: KakaoMap; position: KakaoLatLng; title?: string }) => KakaoMarker;
      };
    };
  }
}

interface KakaoMap {
  setCenter: (latlng: KakaoLatLng) => void;
  setLevel: (level: number) => void;
  getCenter: () => KakaoLatLng;
  getLevel: () => number;
}

interface KakaoLatLng {
  getLat: () => number;
  getLng: () => number;
}

interface KakaoMarker {
  setPosition: (latlng: KakaoLatLng) => void;
  setMap: (map: KakaoMap | null) => void;
}

let mapInstance: KakaoMap | null = null;
let markerInstance: KakaoMarker | null = null;

/**
 * Initialize Kakao Map in the specified container
 */
export function initKakaoMap(
  containerId: string,
  options: KakaoMapOptions
): Promise<KakaoMap | null> {
  return new Promise((resolve) => {
    if (!window.kakao?.maps) {
      console.warn('Kakao Maps SDK not loaded');
      resolve(null);
      return;
    }

    window.kakao.maps.load(() => {
      const container = document.getElementById(containerId);
      if (!container) {
        console.warn(`Container #${containerId} not found`);
        resolve(null);
        return;
      }

      const center = new window.kakao!.maps.LatLng(
        options.center.lat,
        options.center.lng
      );

      const map = new window.kakao!.maps.Map(container, {
        center,
        level: options.level ?? 3,
      });

      mapInstance = map;
      resolve(map);
    });
  });
}

/**
 * Create a marker on the map
 */
export function createMarker(
  map: KakaoMap,
  options: KakaoMarkerOptions
): KakaoMarker | null {
  if (!window.kakao?.maps) {
    return null;
  }

  const position = new window.kakao.maps.LatLng(
    options.position.lat,
    options.position.lng
  );

  const marker = new window.kakao.maps.Marker({
    map,
    position,
    title: options.title,
  });

  // Remove previous marker
  if (markerInstance) {
    markerInstance.setMap(null);
  }
  markerInstance = marker;

  return marker;
}

/**
 * Set map center to specified coordinates
 */
export function setCenter(
  map: KakaoMap,
  lat: number,
  lng: number
): void {
  if (!window.kakao?.maps) {
    return;
  }

  const center = new window.kakao.maps.LatLng(lat, lng);
  map.setCenter(center);
}

/**
 * Get the current map instance
 */
export function getMapInstance(): KakaoMap | null {
  return mapInstance;
}

/**
 * Get the current marker instance
 */
export function getMarkerInstance(): KakaoMarker | null {
  return markerInstance;
}

/**
 * Clear the current marker
 */
export function clearMarker(): void {
  if (markerInstance) {
    markerInstance.setMap(null);
    markerInstance = null;
  }
}

/**
 * Check if Kakao Maps SDK is loaded
 */
export function isKakaoMapsLoaded(): boolean {
  return !!window.kakao?.maps;
}
