#pragma once

// Devices on the control page, in knob order.
// Index 0-2 are HA lights, 3 is the music player, 4 is the local screen backlight.
// The light entities must match the packages in voice-clock.yaml. The music player
// entity is the ${music_player} substitution in voice-clock.yaml.
namespace vc {

static const int DEVICE_COUNT = 5;
static const int MUSIC_IDX = 3;
static const int SCREEN_IDX = 4;

static const char *const NAMES[DEVICE_COUNT] = {
    "Lamp 1",
    "Lamp 2",
    "Reading light",
    "Music",
    "Screen",
};

static const char *const ENTITIES[DEVICE_COUNT] = {
    "light.lamp_1",
    "light.lamp_2",
    "light.reading_light",
    "",  // see ${music_player}
    "",
};

// Ignore HA state echoes for this long after a local change, so the arc doesn't jump back mid-turn.
static const uint32_t ECHO_IGNORE_MS = 1500;

}  // namespace vc
