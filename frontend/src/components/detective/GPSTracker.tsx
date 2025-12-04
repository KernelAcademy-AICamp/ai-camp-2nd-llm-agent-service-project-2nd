/**
 * GPSTracker Component
 * 003-role-based-ui Feature - US5 (T099)
 *
 * GPS location tracking component for detective field work.
 * Integrates with Kakao Maps for visualization.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { initKakaoMap, createMarker, setCenter, isKakaoMapsLoaded } from '@/lib/kakao-maps';

interface LocationData {
  latitude: number;
  longitude: number;
  accuracy: number;
  timestamp: number;
}

interface GPSTrackerProps {
  onLocationSave: (location: LocationData) => void;
  onError?: (error: string) => void;
  className?: string;
}

export default function GPSTracker({
  onLocationSave,
  onError,
  className = '',
}: GPSTrackerProps) {
  const [location, setLocation] = useState<LocationData | null>(null);
  const [isTracking, setIsTracking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [geolocationSupported, setGeolocationSupported] = useState(true);

  const watchIdRef = useRef<number | null>(null);
  const mapRef = useRef<unknown>(null);

  // Check geolocation support on mount
  useEffect(() => {
    if (!navigator.geolocation) {
      setGeolocationSupported(false);
      setError('GPS를 지원하지 않는 브라우저입니다. 위치 서비스를 사용할 수 없습니다.');
    }
  }, []);

  // Initialize map
  useEffect(() => {
    if (isKakaoMapsLoaded() && !mapRef.current) {
      initKakaoMap('gps-map', {
        center: { lat: 37.5665, lng: 126.978 }, // Seoul default
        level: 3,
      }).then((map) => {
        mapRef.current = map;
      });
    }
  }, []);

  // Update map when location changes
  useEffect(() => {
    if (location && mapRef.current) {
      setCenter(mapRef.current as Parameters<typeof setCenter>[0], location.latitude, location.longitude);
      createMarker(mapRef.current as Parameters<typeof createMarker>[0], {
        position: { lat: location.latitude, lng: location.longitude },
        title: '현재 위치',
      });
    }
  }, [location]);

  // Cleanup watch on unmount
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  const handleError = useCallback(
    (geoError: GeolocationPositionError) => {
      let message = '위치 정보를 가져오는데 실패했습니다.';

      switch (geoError.code) {
        case 1:
          message = '위치 접근이 거부되었습니다. 위치 권한을 허용해 주세요.';
          break;
        case 2:
          message = '위치 정보를 사용할 수 없습니다.';
          break;
        case 3:
          message = '위치 정보 요청 시간이 초과되었습니다.';
          break;
      }

      setError(message);
      setIsLoading(false);
      onError?.(message);
    },
    [onError]
  );

  const getCurrentPosition = useCallback(() => {
    if (!navigator.geolocation) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setSaved(false);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const locationData: LocationData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp,
        };
        setLocation(locationData);
        setIsLoading(false);
      },
      handleError,
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  }, [handleError]);

  const startTracking = useCallback(() => {
    if (!navigator.geolocation) {
      return;
    }

    setIsTracking(true);
    setError(null);
    setSaved(false);

    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        const locationData: LocationData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp,
        };
        setLocation(locationData);
      },
      handleError,
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 5000,
      }
    );
  }, [handleError]);

  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setIsTracking(false);
  }, []);

  const saveLocation = useCallback(() => {
    if (location) {
      onLocationSave(location);
      setSaved(true);
    }
  }, [location, onLocationSave]);

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  if (!geolocationSupported) {
    return (
      <div className={`p-4 bg-[var(--color-bg-secondary)] rounded-lg ${className}`}>
        <h3 className="text-lg font-semibold mb-4">GPS 위치 추적</h3>
        <div className="text-[var(--color-error)] p-4 bg-red-50 rounded-lg">
          GPS를 지원하지 않는 브라우저입니다. 위치 서비스를 사용할 수 없습니다.
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 bg-[var(--color-bg-secondary)] rounded-lg ${className}`}>
      <h3 className="text-lg font-semibold mb-4">GPS 위치 추적</h3>

      {/* Map Container */}
      <div
        id="gps-map"
        className="h-64 w-full rounded-lg bg-gray-200 mb-4"
        aria-label="지도"
      />

      {/* Controls */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          type="button"
          onClick={getCurrentPosition}
          disabled={isLoading || isTracking}
          className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg
            hover:bg-[var(--color-primary-hover)] disabled:opacity-50
            disabled:cursor-not-allowed min-h-[44px]"
        >
          {isLoading ? '위치 확인 중...' : '현재 위치 가져오기'}
        </button>

        {!isTracking ? (
          <button
            type="button"
            onClick={startTracking}
            disabled={isLoading}
            className="px-4 py-2 bg-[var(--color-secondary)] text-white rounded-lg
              hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
          >
            위치 추적 시작
          </button>
        ) : (
          <button
            type="button"
            onClick={stopTracking}
            className="px-4 py-2 bg-[var(--color-error)] text-white rounded-lg
              hover:opacity-90 min-h-[44px]"
          >
            추적 중지
          </button>
        )}

        <button
          type="button"
          onClick={saveLocation}
          disabled={!location}
          className="px-4 py-2 bg-green-600 text-white rounded-lg
            hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
        >
          위치 저장
        </button>
      </div>

      {/* Tracking Indicator */}
      {isTracking && (
        <div className="flex items-center gap-2 text-[var(--color-primary)] mb-4">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-primary)] opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-[var(--color-primary)]" />
          </span>
          <span>추적 중...</span>
        </div>
      )}

      {/* Location Info */}
      {location && (
        <div className="bg-white p-4 rounded-lg border border-[var(--color-border)]">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-[var(--color-text-secondary)] text-sm">위도</span>
              <p className="font-mono text-lg">{location.latitude.toFixed(6)}</p>
            </div>
            <div>
              <span className="text-[var(--color-text-secondary)] text-sm">경도</span>
              <p className="font-mono text-lg">{location.longitude.toFixed(6)}</p>
            </div>
            <div>
              <span className="text-[var(--color-text-secondary)] text-sm">정확도 (accuracy)</span>
              <p className="font-mono">{location.accuracy.toFixed(1)}m</p>
            </div>
            <div>
              <span className="text-[var(--color-text-secondary)] text-sm">시간</span>
              <p className="font-mono">{formatTimestamp(location.timestamp)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-[var(--color-error)] rounded-lg">
          {error}
        </div>
      )}

      {/* Success Message */}
      {saved && (
        <div className="mt-4 p-3 bg-green-50 text-green-700 rounded-lg">
          위치가 저장 완료되었습니다.
        </div>
      )}
    </div>
  );
}
