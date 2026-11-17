-- SPDX-License-Identifier: MIT
-- DoD Fighter — the launch screen without LF2's leftovers: no credit lines
-- (bottom right), no version label (top right) and no "official website" entry
-- (the menu picture is drawn without that line and its highlight is skipped; the
-- sheet itself stays whole, since the "options" entry is spelled from its letters;
-- clicking where it was, or any website link, does nothing).

local WEBSITES = {open_website = true, open_original_website = true,
    open_marti_website = true, open_starsky_website = true}

return function(base)
    local create, update = base.create, base.update

    function base.create(options)
        local state = create(options)
        state.credits = {}
        return state
    end

    function base.update(state, flow_input, context)
        local proxy = {}
        for key, value in pairs(context) do proxy[key] = value end
        function proxy.action(name, ...)
            if WEBSITES[name] then return end
            return context.action(name, ...)
        end
        local result = update(state, flow_input, proxy)
        -- the version label (engine.build_label) is the only text drawn at the top right
        local kept = {}
        for _, command in ipairs(state.display) do
            local rect = command[1] == "sprite" and command[2] == "pe/menu_clip5" and command[3]
            if command[1] == "text" and command[2] == engine.build_label then
                -- dropped
            elseif rect and rect[1] == 285 and rect[2] == 32 then
                -- the highlighted "official website": dropped
            elseif rect and rect[1] == 0 and rect[2] == 0 and rect[4] == 181 then
                -- the menu list: its first four lines only (the fifth, at y 136-172, is the website)
                local copy = {}
                for key, value in pairs(command) do copy[key] = value end
                copy[3] = {0, 0, rect[3], 136}
                kept[#kept + 1] = copy
            else
                kept[#kept + 1] = command
            end
        end
        state.display = kept
        return result
    end

    return base
end
