// Define interfaces
const Track = {
    id: "",
    name: "",
    duration: 0,
    isLocal: false,
    album: {
        id: "",
        name: "",
        image: {
            height: 0,
            width: 0,
            url: ""
        }
    },
    artists: []
};

const Device = {
    id: "",
    is_active: false
};

// Define constants
const API_BASE = "https://api.spotify.com/v1/me/player";

// Define SpotifyStore class
class SpotifyStore {
    constructor() {
        this.track = null;
        this.device = null;
        this.isPlaying = false;
        this.repeat = "off";
        this.shuffle = false;
        this.volume = 0;
        this.isSettingPosition = false;
        this.mPosition = 0;
        this.start = 0;
    }

    get position() {
        let pos = this.mPosition;
        if (this.isPlaying) {
            pos += Date.now() - this.start;
        }
        return pos;
    }

    set position(p) {
        this.mPosition = p;
        this.start = Date.now();
    }

    // Methods
    prev() {
        this.req("post", "/previous");
    }

    next() {
        this.req("post", "/next");
    }

    setVolume(percent) {
        this.req("put", "/volume", {
            query: {
                volume_percent: Math.round(percent)
            }
        }).then(() => {
            this.volume = percent;
            this.emitChange();
        });
    }

    setPlaying(playing) {
        this.req("put", playing ? "/play" : "/pause");
    }

    setRepeat(state) {
        this.req("put", "/repeat", {
            query: { state }
        });
    }

    setShuffle(state) {
        this.req("put", "/shuffle", {
            query: { state }
        }).then(() => {
            this.shuffle = state;
            this.emitChange();
        });
    }

    seek(ms) {
        if (this.isSettingPosition) return Promise.resolve();

        this.isSettingPosition = true;

        return this.req("put", "/seek", {
            query: {
                position_ms: Math.round(ms)
            }
        }).catch((e) => {
            console.error("[VencordSpotifyControls] Failed to seek", e);
            this.isSettingPosition = false;
        });
    }

    req(method, route, data = {}) {
        if (this.device?.is_active) {
            data.query = data.query || {};
            data.query.device_id = this.device.id;
        }

        // Perform HTTP request here
        console.log(`Performing ${method} request to ${API_BASE}${route} with data:`, data);
    }

    emitChange() {
        // Implement your own change event emitter logic here
        console.log("Change emitted");
    }
}

// Usage
const spotifyStore = new SpotifyStore();

// Example usage
spotifyStore.prev(); // Example of calling the prev() method
