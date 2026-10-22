using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Web.Script.Serialization;
using System.Collections.Generic;

public sealed class SetupForm : HostForm {
    TextBox Folder=new TextBox();
    CheckBox Voice=new CheckBox(), Transcription=new CheckBox(), Launch=new CheckBox();
    Label Gpu=new Label(), Notice=new Label(), Status=new Label();
    string Failure="";
    Button Details=new Button();
    bool Expanded;
    bool Completed;
    public SetupForm():base("VH Embodiment Server Setup") {
        ClientSize=new Size(790,740);MinimumSize=new Size(806,779);
        Heading.Text="VH Embodiment Server";
        Description.Text="Everything needed for the virtual human and course notebooks.";
        Controls.Add(new Label{Text="What will be installed",Left=28,Top=123,Width=734,Font=new Font(Font,FontStyle.Bold)});
        Controls.Add(new Label{Text="Application and speech models  >  installation/",Left=28,Top=159,Width=734});
        Controls.Add(new Label{Text="Shared Python environment  >  .venv-vh-course/",Left=28,Top=194,Width=734});
        Controls.Add(new Label{Text="The same environment runs both servers and the course notebooks.",Left=28,Top=221,Width=734,ForeColor=Color.FromArgb(75,92,110)});
        Controls.Add(new Label{Text="Speech recognition: Whisper Small + Tiny.\nVoices: English and Italian, female and male (four Piper models).",Left=28,Top=265,Width=734,Height=48});
        Controls.Add(new Label{Text="Application folder (inside virtual_human_project)",Left=28,Top=327,Width=734});
        Folder.SetBounds(28,354,734,56);
        Folder.Text=Path.Combine(RepositoryRoot(),"virtual_human_project","installation");
        Folder.ReadOnly=true;Folder.Multiline=true;Folder.WordWrap=true;Folder.ScrollBars=ScrollBars.Vertical;
        Status.SetBounds(28,618,734,40);Status.Text="Ready to install.";Status.Font=new Font(Font,FontStyle.Bold);Status.Anchor=AnchorStyles.Bottom|AnchorStyles.Left|AnchorStyles.Right;Controls.Add(Status);
        Progress.SetBounds(28,596,734,12);
        Notice.SetBounds(28,660,734,35);Notice.Anchor=AnchorStyles.Bottom|AnchorStyles.Left|AnchorStyles.Right;Notice.Text="Setup downloads everything now. Local speech needs no downloads during use.";
        Notice.ForeColor=Color.FromArgb(75,92,110);Controls.Add(Notice);
        Controls.Add(new Label{Text="Optional NVIDIA acceleration",Left=28,Top=464,Width=734,Font=new Font(Font,FontStyle.Bold)});
        Gpu.SetBounds(28,491,734,28);Gpu.Text="Detecting GPU...";
        Voice.SetBounds(28,522,360,26);Voice.Text="Accelerate voice generation";
        Transcription.SetBounds(408,522,354,26);Transcription.Text="Accelerate speech recognition";
        Voice.Enabled=Transcription.Enabled=false;
        Launch.SetBounds(28,562,400,30);Launch.Text="Launch after installation";Launch.Checked=true;
        Details.SetBounds(620,562,142,30);Details.Text="Show details";
        Details.Click+=(s,e)=>ToggleDetails();
        Logs.SetBounds(28,605,734,145);Logs.Anchor=AnchorStyles.Top|AnchorStyles.Left|AnchorStyles.Right;Logs.Visible=false;
        Controls.AddRange(new Control[]{Folder,Voice,Transcription,Gpu,Launch,Details});
        MainButton.Text="Install";MainButton.Click+=async(s,e)=>await Install();
        Shown+=async(s,e)=>await Detect();
        FormClosing+=(s,e)=>{
            if(Running && MessageBox.Show("Cancel setup? Downloaded files will be kept for the next attempt.","Installation in progress",MessageBoxButtons.YesNo)!=DialogResult.Yes)e.Cancel=true;
        };
    }
    void ToggleDetails() {
        Expanded=!Expanded;Logs.Visible=Expanded;
        Details.Text=Expanded?"Hide details":"Show details";
        ClientSize=new Size(ClientSize.Width,Expanded?910:740);
    }
    protected override void Log(string message) {
        if(IsDisposed)return;
        if(InvokeRequired){BeginInvoke(new Action<string>(Log),message);return;}
        base.Log(message);
        if(!Running || message==null)return;
        if(message.StartsWith("Download ") && !message.StartsWith("Download retry") && !message.StartsWith("Download failed"))Status.Text="Downloading "+message.Substring(9);
        else if(message.StartsWith("  ") && message.Contains("%"))Status.Text="Downloading "+message.Trim();
        else if(message.StartsWith("Download retry")) {
            Notice.Text="Connection interrupted. Retrying automatically; downloaded files are kept.";
            Notice.ForeColor=Color.FromArgb(145,85,0);
            Status.Text=message.Split(new[]{": "},2,StringSplitOptions.None)[0]+" - please wait...";
        } else if(message.StartsWith("NVIDIA setup failed")) {
            Notice.Text="GPU acceleration failed. Setup is continuing on CPU.";
            Notice.ForeColor=Color.FromArgb(145,85,0);
        } else if(message.StartsWith("ERROR: Download incomplete:") || (message.StartsWith("ERROR:") && message.Contains("urlopen error"))) {
            Failure="Download interrupted. Click Retry to resume the missing files.";
        }

        if(message.StartsWith("Preparing files"))Status.Text="Preparing application files...";
        else if(message.StartsWith("[Package"))Status.Text="Downloading Python packages...";
        else if(message.StartsWith("[Model"))Status.Text="Downloading speech models...";
        else if(message.StartsWith("Creating the shared"))Status.Text="Creating the shared course environment...";
        else if(message.StartsWith("Installing"))Status.Text="Installing course dependencies...";
        else if(message.StartsWith("Checking imports"))Status.Text="Testing speech recognition and all four voices...";
    }
    static string RepositoryRoot() {
        for(var current=new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory);current!=null;current=current.Parent) {
            if(File.Exists(Path.Combine(current.FullName,"requirements.txt")) &&
               File.Exists(Path.Combine(current.FullName,"virtual_human_project","vh_cognitive_architecture_server","vh_cognitive_server.py")))return current.FullName;
        }
        throw new Exception("Open this installer from inside the cloned course repository.");
    }
    async Task Detect() {
        string result=await Task.Run(()=>{
            try {
                var p=Process.Start(new ProcessStartInfo("nvidia-smi","--query-gpu=name --format=csv,noheader") {UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true});
                if(!p.WaitForExit(10000)){p.Kill();return "";}
                string name=p.StandardOutput.ReadToEnd();return p.ExitCode==0?name.Trim():"";
            }catch{return "";}
        });
        if(IsDisposed)return;
        Voice.Enabled=Transcription.Enabled=!Running && result.Length>0;
        Gpu.Text=result.Length>0?"Detected GPU: "+result:"No compatible NVIDIA GPU detected. Speech will use CPU.";
    }
    public static void Extract(string destination) {
        Directory.CreateDirectory(destination);
        string prefix=Path.GetFullPath(destination).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        using(var resource=Assembly.GetExecutingAssembly().GetManifestResourceStream("app.zip"))
        using(var archive=new ZipArchive(resource,ZipArchiveMode.Read)) {
            foreach(var item in archive.Entries) {
                string path=Path.GetFullPath(Path.Combine(prefix,item.FullName));
                if(!path.StartsWith(prefix,StringComparison.OrdinalIgnoreCase))throw new Exception("Invalid package path.");
                if(String.IsNullOrEmpty(item.Name)){Directory.CreateDirectory(path);continue;}
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                string temporary=path+".setup-new";
                using(var input=item.Open())using(var output=File.Create(temporary))input.CopyTo(output);
                if(File.Exists(path))File.Replace(temporary,path,null);else File.Move(temporary,path);
            }
        }
    }
    async Task Install() {
        if(Completed){Close();return;}
        bool success=false;
        try {
            string target=Path.GetFullPath(Folder.Text.Trim());
            // No extraction while an existing installed server is running.
            foreach(var p in Process.GetProcessesByName("VirtualHuman")) {
                try {if(Path.GetDirectoryName(p.MainModule.FileName).Equals(target,StringComparison.OrdinalIgnoreCase))throw new InvalidOperationException("Close VH Embodiment Server before updating this folder.");}
                catch(System.ComponentModel.Win32Exception){}
            }
            var drive=new DriveInfo(Path.GetPathRoot(target));
            if(drive.AvailableFreeSpace<1024L*1024*1024)throw new Exception("At least 1 GB free is required to start. Setup checks the additional space before downloading models.");
            Failure="";Heading.Text="VH Embodiment Server";Status.ForeColor=Color.Black;
            Notice.Text="Setup downloads everything now. Local speech needs no downloads during use.";Notice.ForeColor=Color.FromArgb(75,92,110);
            bool voice=Voice.Checked, transcription=Transcription.Checked;
            Running=true;MainButton.Enabled=false;Voice.Enabled=Transcription.Enabled=false;
            ExitButton.Text="Cancel";Progress.Style=ProgressBarStyle.Marquee;
            Log("Preparing files in "+target);
            await Task.Run(()=>Extract(target));
            string command="-NoProfile -ExecutionPolicy Bypass -File "+Quote(Path.Combine(target,"setup.ps1"))+
                " -Yes -Profile "+(voice||transcription?"gpu":"cpu")+
                " -VoiceDevice "+(voice?"auto":"cpu")+" -TranscriptionDevice "+(transcription?"auto":"cpu");
            int code=await Execute("powershell.exe",command,target);
            if(code!=0)throw new Exception("Installation incomplete. Open Show details, fix the issue and click Retry. Verified downloads will be reused.");
            Completed=success=true;Heading.Text="Installation complete";
            Notice.Text="Installation completed. Downloaded files have been verified.";Notice.ForeColor=Color.FromArgb(75,92,110);
            Status.Text="Speech and transcription verified. Launch VirtualHuman.exe from the application folder next time.";
            string resultFile=Path.Combine(target,"setup-result.json");
            if(File.Exists(resultFile)) {
                var result=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(resultFile));
                if(result.ContainsKey("gpu_warning")) {
                    Notice.Text="GPU acceleration failed. You can retry setup later; CPU mode is ready.";Notice.ForeColor=Color.FromArgb(145,85,0);
                    Heading.Text="VH Embodiment Server";Status.Text="GPU acceleration is unavailable. The application is ready on CPU.";
                    Log("Optional GPU: "+result["gpu_warning"]);
                }
            }
            MainButton.Text="Finish";ExitButton.Text="Close";
            if(Launch.Checked)Open(Path.Combine(target,"VirtualHuman.exe"));
        }catch(Exception ex){Log("ERROR: "+ex.Message);Heading.Text="VH Embodiment Server";Status.ForeColor=Color.Firebrick;
            Notice.Text="Downloaded files are kept. Nothing needs to be deleted.";Notice.ForeColor=Color.Firebrick;
            Status.Text=Failure.Length>0?Failure:"Setup could not finish. See details, then click Retry.";if(!Expanded)ToggleDetails();MainButton.Text="Retry";}
        finally {
            Running=false;MainButton.Enabled=true;Progress.Style=ProgressBarStyle.Blocks;Progress.Value=success?100:0;
        }
        if(!success)await Detect();
    }
    [STAThread] public static int Main(string[] args) {
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
        if(!Environment.Is64BitOperatingSystem) {
            MessageBox.Show("This version requires 64-bit Windows for local speech and transcription. No components were downloaded.","Unsupported system");
            return 1;
        }
        try {
            if(args.Length==2 && args[0]=="--extract-only"){Extract(Path.GetFullPath(args[1]));return 0;}
            using(var form=new SetupForm()) {
                if(args.Length==2 && args[0]=="--snapshot"){form.Snapshot(args[1]);return 0;}
                Application.Run(form);
            }return 0;
        }catch(Exception ex){MessageBox.Show(ex.Message,"VH Embodiment Server");return 1;}
    }
}