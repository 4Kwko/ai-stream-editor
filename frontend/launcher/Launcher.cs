// Lançador do AI Stream Editor para este PC (Windows).
// Não instala nada: usa o ambiente já preparado (backend\.venv e frontend\node_modules)
// e o inicializador do backend (python -m ai_stream_editor.local), que reutiliza
// serviços já em execução e só encerra o que ele mesmo iniciou.
// Compilar: node launcher/build.mjs (dentro de frontend/).

using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Threading;

internal static class Launcher
{
    private const string AppUrl = "http://127.0.0.1:5173/";
    private const string HealthUrl = "http://127.0.0.1:8765/api/health";
    private const int ReadyTimeoutSeconds = 90;

    private static int Main()
    {
        Console.Title = "AI Stream Editor";
        try
        {
            return Run();
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("Erro inesperado: " + error.Message);
            return Fail();
        }
    }

    private static int Run()
    {
        string root = FindProjectRoot();
        if (root == null)
        {
            Console.Error.WriteLine("Não encontrei a pasta do projeto (backend\\ai_stream_editor) acima de:");
            Console.Error.WriteLine("  " + AppDomain.CurrentDomain.BaseDirectory);
            Console.Error.WriteLine("Mantenha o .exe dentro da pasta do projeto ou use um atalho para ele.");
            return Fail();
        }

        if (IsBackendReady() && IsInterfaceReady())
        {
            Console.WriteLine("O AI Stream Editor já está em execução. Abrindo no navegador…");
            OpenBrowser();
            Thread.Sleep(1500);
            return 0;
        }

        string python = Path.Combine(root, "backend", ".venv", "Scripts", "python.exe");
        if (!File.Exists(python))
        {
            Console.Error.WriteLine("Ambiente do backend ausente: " + python);
            Console.Error.WriteLine("Prepare-o com scripts\\setup-backend.ps1 (veja backend\\README.md).");
            return Fail();
        }

        Console.WriteLine("Iniciando o AI Stream Editor…");
        Console.WriteLine("Deixe esta janela aberta enquanto usa o app. Fechar a janela encerra os serviços iniciados por ela.");
        Console.WriteLine();

        var start = new ProcessStartInfo(python, "-m ai_stream_editor.local")
        {
            WorkingDirectory = Path.Combine(root, "backend"),
            UseShellExecute = false,
        };
        start.EnvironmentVariables["PYTHONUTF8"] = "1";

        using (Process starter = Process.Start(start))
        {
            if (!WaitUntilReady(starter))
            {
                if (starter.HasExited)
                {
                    Console.Error.WriteLine();
                    Console.Error.WriteLine("O inicializador terminou antes de o app ficar pronto. Veja a mensagem acima.");
                    return Fail();
                }
                Console.Error.WriteLine("O app não respondeu em " + ReadyTimeoutSeconds + " s. A janela continua aberta para você ver a saída.");
            }
            else
            {
                Console.WriteLine();
                Console.WriteLine("Pronto. Abrindo " + AppUrl);
                OpenBrowser();
            }

            starter.WaitForExit();
            if (starter.ExitCode != 0)
            {
                Console.Error.WriteLine();
                Console.Error.WriteLine("O AI Stream Editor parou com erro (código " + starter.ExitCode + ").");
                return Fail();
            }
            return 0;
        }
    }

    /// <summary>Sobe a partir da pasta do .exe até achar a raiz do projeto.</summary>
    private static string FindProjectRoot()
    {
        var dir = new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "backend", "ai_stream_editor", "local.py")) &&
                Directory.Exists(Path.Combine(dir.FullName, "frontend")))
            {
                return dir.FullName;
            }
            dir = dir.Parent;
        }
        return null;
    }

    private static bool WaitUntilReady(Process starter)
    {
        DateTime deadline = DateTime.UtcNow.AddSeconds(ReadyTimeoutSeconds);
        while (DateTime.UtcNow < deadline)
        {
            if (starter.HasExited) return false;
            if (IsBackendReady() && IsInterfaceReady()) return true;
            Thread.Sleep(500);
        }
        return false;
    }

    private static bool IsBackendReady()
    {
        string body = Get(HealthUrl);
        return body != null && body.Contains("\"status\"");
    }

    /// <summary>Confere que a porta 5173 serve esta interface, não outro programa.</summary>
    private static bool IsInterfaceReady()
    {
        string body = Get(AppUrl);
        return body != null && body.Contains("<title>AI Stream Editor</title>");
    }

    private static string Get(string url)
    {
        try
        {
            var request = (HttpWebRequest)WebRequest.Create(url);
            request.Timeout = 2000;
            request.Proxy = null;
            using (var response = (HttpWebResponse)request.GetResponse())
            using (var reader = new StreamReader(response.GetResponseStream()))
            {
                return reader.ReadToEnd();
            }
        }
        catch (WebException)
        {
            return null;
        }
    }

    private static void OpenBrowser()
    {
        Process.Start(new ProcessStartInfo(AppUrl) { UseShellExecute = true });
    }

    private static int Fail()
    {
        Console.Error.WriteLine();
        Console.Error.WriteLine("Pressione Enter para fechar.");
        Console.ReadLine();
        return 1;
    }
}
