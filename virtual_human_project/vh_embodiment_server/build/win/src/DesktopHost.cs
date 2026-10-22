using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows.Forms;

// Windows owns the whole process tree: closing either window also stops children.
public sealed class ProcessJob : IDisposable {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr a, string n);
    [DllImport("kernel32.dll")] static extern bool SetInformationJobObject(IntPtr j, int c, IntPtr p, uint n);
    [DllImport("kernel32.dll")] static extern bool AssignProcessToJobObject(IntPtr j, IntPtr p);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [StructLayout(LayoutKind.Sequential)] struct Basic {
        public long ProcessTime, JobTime; public uint Flags; public UIntPtr Min, Max;
        public uint Active; public UIntPtr Affinity; public uint Priority, Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)] struct IO { public ulong a,b,c,d,e,f; }
    [StructLayout(LayoutKind.Sequential)] struct Extended {
        public Basic Basic; public IO IO; public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob;
    }
    IntPtr handle;
    public ProcessJob() {
        handle=CreateJobObject(IntPtr.Zero,null);
        var info=new Extended(); info.Basic.Flags=0x2000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        int size=Marshal.SizeOf(info); IntPtr buffer=Marshal.AllocHGlobal(size);
        try {
            Marshal.StructureToPtr(info,buffer,false);
            if(handle==IntPtr.Zero || !SetInformationJobObject(handle,9,buffer,(uint)size))
                throw new Exception("Cannot initialize process management.");
        } finally { Marshal.FreeHGlobal(buffer); }
    }
    public void Add(Process process) {
        if(!AssignProcessToJobObject(handle,process.Handle)) {
            try { process.Kill(); } catch {}
            throw new Exception("Cannot attach the process to this window. Launch cancelled.");
        }
    }
    public void Dispose() { if(handle!=IntPtr.Zero){CloseHandle(handle);handle=IntPtr.Zero;} }
}

public class HostForm : Form {
    protected TextBox Logs=new TextBox();
    protected Label Heading=new Label(), Description=new Label();
    protected ProgressBar Progress=new ProgressBar();
    protected Button MainButton=new Button(), ExitButton=new Button();
    protected ProcessJob Job;
    protected Process Child;
    protected bool Running;
    public HostForm(string title) {
        Text=title;Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath); ClientSize=new Size(790,660); MinimumSize=new Size(806,699);
        StartPosition=FormStartPosition.CenterScreen; Font=new Font("Segoe UI",10);
        BackColor=Color.FromArgb(242,245,249); AutoScaleMode=AutoScaleMode.Dpi;
        var brand=new PictureBox{Left=28,Top=23,Width=48,Height=48,SizeMode=PictureBoxSizeMode.Zoom,Image=Icon.ToBitmap()};Controls.Add(brand);
        Heading.SetBounds(90,22,670,38);Heading.Font=new Font("Segoe UI",19,FontStyle.Bold);
        Description.SetBounds(30,80,725,42);
        Logs.SetBounds(28,365,734,220); Logs.Multiline=true;Logs.ReadOnly=true;
        Logs.ScrollBars=ScrollBars.Vertical;Logs.Font=new Font("Consolas",9);
        Logs.Anchor=AnchorStyles.Top|AnchorStyles.Bottom|AnchorStyles.Left|AnchorStyles.Right;
        Progress.SetBounds(28,596,734,12);Progress.Anchor=AnchorStyles.Bottom|AnchorStyles.Left|AnchorStyles.Right;
        MainButton.SetBounds(520,620,132,30);MainButton.Anchor=AnchorStyles.Bottom|AnchorStyles.Right;
        ExitButton.SetBounds(662,620,100,30);ExitButton.Text="Close";ExitButton.Anchor=AnchorStyles.Bottom|AnchorStyles.Right;
        ExitButton.Click+=(s,e)=>Close();
        Controls.AddRange(new Control[]{Heading,Description,Logs,Progress,MainButton,ExitButton});
    }
    protected override void OnFormClosing(FormClosingEventArgs e) {
        base.OnFormClosing(e);
        if(!e.Cancel && Job!=null)Job.Dispose();
    }
    protected virtual void Log(string message) {
        if(message==null || IsDisposed)return;
        if(InvokeRequired){BeginInvoke(new Action<string>(Log),message);return;}
        Logs.AppendText(message+Environment.NewLine);
    }
    protected async Task<int> Execute(string file, string arguments, string cwd) {
        Job=new ProcessJob();
        var start=new ProcessStartInfo(file,arguments){WorkingDirectory=cwd,UseShellExecute=false,
            CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
        start.EnvironmentVariables["PYTHONUTF8"]="1";start.EnvironmentVariables["PYTHONUNBUFFERED"]="1";
        start.StandardOutputEncoding=System.Text.Encoding.UTF8;start.StandardErrorEncoding=System.Text.Encoding.UTF8;
        Child=new Process{StartInfo=start};
        Child.OutputDataReceived+=(s,e)=>Log(e.Data);Child.ErrorDataReceived+=(s,e)=>Log(e.Data);
        Child.Start();Job.Add(Child);Child.BeginOutputReadLine();Child.BeginErrorReadLine();
        await Task.Run(()=>Child.WaitForExit());
        int code=Child.ExitCode; Job.Dispose();Job=null;return code;
    }
    public static string Quote(string value) { return "\""+value.Replace("\"", "")+"\""; }
    public static void Open(string target) { Process.Start(new ProcessStartInfo(target){UseShellExecute=true}); }
    public void Snapshot(string path) {
        Show();Application.DoEvents();
        using(var bitmap=new Bitmap(Width,Height)){DrawToBitmap(bitmap,new Rectangle(0,0,Width,Height));bitmap.Save(path);}
        Close();
    }
}
