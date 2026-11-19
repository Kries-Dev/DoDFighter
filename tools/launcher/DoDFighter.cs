// DoD Fighter launcher: double-click to start OpenLF2 with the darthnox mod.
// Built by tools/make_package.ps1 (C# compiler that ships with Windows).
//
// Everything stays in the game folder: settings and the original LF2 installer
// live in .\config (--config-dir). On the first start OpenLF2 offers to download
// the LF2 installer there itself.
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

static class Launcher
{
    [STAThread]
    static void Main(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string exe = Path.Combine(root, "openlf2.exe");
        string mod = Path.Combine(root, "mods", "darthnox", "package.manifest");
        if (!File.Exists(exe) || !File.Exists(mod))
        {
            MessageBox.Show("openlf2.exe or mods\\darthnox is missing next to this launcher.\n" +
                            "Unzip the whole DoD Fighter folder and start it from there.",
                            "DoD Fighter", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        string config = Path.Combine(root, "config");
        Directory.CreateDirectory(config);

        string extra = string.Join(" ", Array.ConvertAll(args, a => "\"" + a + "\""));
        var info = new ProcessStartInfo(exe,
            "--mod \"mods\\darthnox\" --config-dir \"" + config.TrimEnd('\\') + "\" " + extra)
        {
            WorkingDirectory = root,
            // a normal window: started from some shells it came up minimized, and the
            // first-run download question was then easy to miss
            UseShellExecute = true,
            WindowStyle = ProcessWindowStyle.Normal,
        };
        Process.Start(info);
    }
}
