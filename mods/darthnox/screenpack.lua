-- SPDX-License-Identifier: MIT
-- DoD Fighter — the Deities of Death screenpack. Every screen draws through
-- flow.draw's context; this hands each screen a context that
--   * swaps LF2's menu sheets (pe/<name>) for ours (mods/darthnox/ui/<name>.bmp,
--     recoloured black / white / red by tools/make_screenpack.py; same layout,
--     so every sprite rectangle still fits) and the loading screen (menu_wait)
--   * draws our backdrop wherever LF2 drew a menu background (pe/menu_backN:
--     launch, title and network screens): storm sky with the reaper, rain
--     (11 frames, keyed) and now and then a lightning flash (sky_flash)
--   * draws our logo (logo.bmp, logo_s.bmp) where LF2 drew its logo strip
--   * recolours the menus' plain fills, clear colours and text colours with the
--     same rule the sheets got (RECOLOUR = make_screenpack.py recolour())
-- Fights (match screen) keep their own colours apart from the swapped sheets.

local UI = "mods/darthnox/ui/"
local SWAPPED = {}
for name in ([[menu_clip menu_clip2 menu_clip3 menu_clip4 menu_clip5 menu_clip6 charmenu battlemode
    battletroops cma cma2 cmc cs2 cs3 cs4 cs5 cs6 frame bars score_board1 score_board2 score_board3
    score_board4 rface pause demo words0 words5 back99_1 back99_2 back99_3 lf2_cursor menu_wait]]):gmatch("%S+") do
    SWAPPED["pe/" .. name] = UI .. name .. ".bmp"
end
local RAIN_FRAMES = 11
local LOGO_W = 440
-- lightning: frame counter positions (of a 300-frame cycle) that show the flash
local FLASH = {[0] = true, [1] = true, [4] = true, [5] = true, [6] = true, [131] = true, [132] = true}

-- LF2 blue -> black / white / red (see tools/make_screenpack.py recolour)
local function hsv(r, g, b)
    r, g, b = r / 255, g / 255, b / 255
    local max, min = math.max(r, g, b), math.min(r, g, b)
    local d = max - min
    local h = 0
    if d > 0 then
        if max == r then h = ((g - b) / d) % 6
        elseif max == g then h = (b - r) / d + 2
        else h = (r - g) / d + 4 end
        h = h / 6
    end
    return h, max > 0 and d / max or 0, max
end
local cache = {}
local function recolour(r, g, b)
    local key = r * 65536 + g * 256 + b
    local hit = cache[key]
    if hit then return hit[1], hit[2], hit[3] end
    local h, s, v = hsv(r, g, b)
    local out
    if s < 0.2 or h < 0.5 or h > 0.75 then out = {r, g, b}
    elseif v >= 0.62 then
        local grey = math.floor(math.min(1, v * 0.95) * 255 + 0.5)
        out = {grey, grey, grey}
    else
        -- hue 0: red = value, green = blue = value * (1 - saturation)
        local sat, val = math.min(1, s * 0.9 + 0.1), v * 0.5
        out = {math.floor(val * 255 + 0.5), math.floor(val * (1 - sat) * 255 + 0.5), math.floor(val * (1 - sat) * 255 + 0.5)}
    end
    cache[key] = out
    return out[1], out[2], out[3]
end
local function recolour_hex(color)
    if type(color) ~= "number" or color < 0 then return color end
    local r, g, b = recolour(math.floor(color / 65536) % 256, math.floor(color / 256) % 256, color % 256)
    return r * 65536 + g * 256 + b
end

return function(base)
    local frame = 0
    local draw = base.draw

    local function wrap(context, menus)
        -- (the script sandbox has no setmetatable: copy the context's functions)
        local proxy = {}
        for key, value in pairs(context) do proxy[key] = value end
        local image, sprite = context.image, context.sprite
        local function backdrop(x, y)
            image(FLASH[frame % 300] and UI .. "sky_flash.bmp" or UI .. "sky.bmp", x, y, false)
            image(UI .. "rain_" .. (frame % RAIN_FRAMES) .. ".bmp", x, y, true)
        end
        function proxy.image(name, x, y, ...)
            if type(name) == "string" then
                if name:match("^pe/menu_back%d+$") then return backdrop(0, y) end
                name = SWAPPED[name] or name
            end
            return image(name, x, y, ...)
        end
        function proxy.sprite(name, rect, x, y, keyed, mirrored, flipped, tint, ...)
            if name == "pe/menu_clip" and rect[2] == 41 then
                -- LF2's logo strip (two pieces: {0,41,434,80} and {434,41,62,68})
                if rect[1] ~= 0 then return end
                if y >= 0x60 then return image(UI .. "logo.bmp", x + 248 - math.floor(LOGO_W / 2), math.max(0, y - 96), true) end
                return image(UI .. "logo_s.bmp", x, y, true)
            end
            -- bitmap-font text (font.gdi) is words0 glyphs with a colour tint
            if menus and tint then tint = recolour_hex(tint) end
            return sprite(SWAPPED[name] or name, rect, x, y, keyed, mirrored, flipped, tint, ...)
        end
        if menus then
            function proxy.viewport(w, h, r, g, b, ...)
                if r then r, g, b = recolour(r, g, b) end
                return context.viewport(w, h, r, g, b, ...)
            end
            function proxy.fill(x, y, w, h, r, g, b, ...)
                if r then r, g, b = recolour(r, g, b) end
                return context.fill(x, y, w, h, r, g, b, ...)
            end
            function proxy.text(text, x, y, align, size, color, color2, background, ...)
                return context.text(text, x, y, align, size, recolour_hex(color), recolour_hex(color2), recolour_hex(background), ...)
            end
        end
        return proxy
    end

    function base.draw(state, context)
        frame = frame + 1
        return draw(state, wrap(context, state.active ~= "match"))
    end

    return base
end
