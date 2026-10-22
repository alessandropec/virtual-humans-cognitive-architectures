using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using System.Collections.Generic;

public sealed class LauncherForm : HostForm {
    string Root=AppDomain.CurrentDomain.BaseDirectory;
    bool OpenBrowser;
    int Port;
    public LauncherForm(bool openBrowser,int port):base("VH Embodiment Server — local server") {
        OpenBrowser=openBrowser;Port=port;
        Heading.Text="VH Embodiment Server";
        Description.Text="This window manages the server. Closing it also stops its child processes.";
        Logs.SetBounds(28,130,734,455);
        MainButton.Text="Start";MainButton.Click+=async(s,e)=>await Start();
        ExitButton.Text="Close all";
        Shown+=async(s,e)=>await Start();
    }
    async Task<bool> Ready() {
        return await Task.Run(()=>{
            try {
                var request=(HttpWebRequest)WebRequest.Create("http://127.0.0.1:"+Port+"/heartbeat");request.Timeout=1000;
                using(var response=request.GetResponse())
                using(var reader=new StreamReader(response.GetResponseStream())) {
                    var data=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(reader.ReadToEnd());
                    return data.ContainsKey("service") && (string)data["service"]=="VH Embodiment Server";
                }
            }catch{return false;}
        });
    }
    async Task Start() {
        if(Running)return;
        try {
            if(await Ready()) {
                Log("Using the VH Embodiment Server already running on port "+Port+".");
                if(OpenBrowser)Open("http://127.0.0.1:"+Port+"/");
                return;
            }
            string config=Path.Combine(Root,"runtime.json");
            if(!File.Exists(config))throw new Exception("Setup incomplete: run the installer before launching.");
            var settings=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(config));
            string python=Path.GetFullPath(Path.Combine(Root,(string)settings["python"]));
            if(!python.Equals(Path.GetFullPath(Path.Combine(Root,"..",".venv-vh-course","Scripts","python.exe")),StringComparison.OrdinalIgnoreCase)||!File.Exists(python))throw new Exception("Runtime not found. Run the installer again.");
            Running=true;MainButton.Enabled=false;Progress.Style=ProgressBarStyle.Marquee;
            Log("Starting server on port "+Port+"...");
            Environment.SetEnvironmentVariable("VH_PORT",Port.ToString());
            Environment.SetEnvironmentVariable("VH_OPEN_BROWSER","0");
            var processTask=Execute(python,"-u "+Quote(Path.Combine(Root,"server.py")),Root);
            bool ready=false;
            for(int i=0;i<60 && !processTask.IsCompleted;i++) {
                if(await Ready()){ready=true;break;}
                await Task.Delay(500);
            }
            if(ready) {
                Progress.Style=ProgressBarStyle.Blocks;Progress.Value=100;
                Description.Text="Server ready. Use the browser application and its API Playground.";
                if(OpenBrowser){Open("http://127.0.0.1:"+Port+"/");}
                Log("Ready. Close the browser tab or this window to stop both local servers.");
            } else if(!processTask.IsCompleted){if(Job!=null)Job.Dispose();throw new Exception("The server did not become ready in time. Read the log.");}
            int exit=await processTask;
            Log("Server stopped (code "+exit+").");Description.Text="Server stopped. Click Start to restart.";
            if(exit==0)Close();
        }catch(Exception ex){Log("ERROR: "+ex.Message);}
        finally {Running=false;MainButton.Enabled=true;Progress.Style=ProgressBarStyle.Blocks;Progress.Value=0;}
    }
    [STAThread] public static int Main(string[] args) {
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
        bool browser=Array.IndexOf(args,"--no-browser")<0;int port=8899;
        int at=Array.IndexOf(args,"--port");if(at>=0)port=int.Parse(args[at+1]);
        string key=AppDomain.CurrentDomain.BaseDirectory.ToLowerInvariant().Replace('\\','_').Replace(':','_');
        bool created;
        using(var mutex=new Mutex(true,"Local\\VirtualHuman_"+key,out created)) {
            if(!created){MessageBox.Show("This copy of VH Embodiment Server is already open.");return 1;}
            using(var form=new LauncherForm(browser,port)){Application.Run(form);}
        }return 0;
    }
}
