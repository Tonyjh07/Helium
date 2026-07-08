import os, uuid, subprocess, time, threading, json, webbrowser
from pathlib import Path
from flask import Flask, request, render_template_string, send_file, jsonify

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

BASE_DIR = Path(__file__).parent
FFMPEG_DIR = BASE_DIR / 'ffmpeg' / 'bin'
FFMPEG = str(FFMPEG_DIR / 'ffmpeg.exe')
FFPROBE = str(FFMPEG_DIR / 'ffprobe.exe')
UPLOAD_DIR = BASE_DIR / 'uploads'
PROCESSED_DIR = BASE_DIR / 'processed'
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.opus'}

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Helium</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f5f5;color:#333;min-height:100vh;display:flex;justify-content:center;align-items:center}
.container{background:#fff;border-radius:12px;padding:36px;width:580px;box-shadow:0 4px 24px rgba(0,0,0,.08)}
h1{font-size:20px;font-weight:600;margin-bottom:6px;text-align:center}
.sub{font-size:13px;color:#999;text-align:center;margin-bottom:18px}
.grp{margin-bottom:16px}
label{display:block;font-size:13px;font-weight:500;margin-bottom:4px;color:#555}
input[type=file]{width:100%;padding:6px 0;font-size:14px}
.row{display:flex;align-items:center;gap:10px}
.row input[type=range]{flex:1;height:6px;accent-color:#4a90d9}
.row .val{min-width:52px;text-align:right;font-size:14px;font-weight:600;color:#222}
.row input[type=text]{width:72px;padding:4px 6px;border:1px solid #ccc;border-radius:4px;font-size:14px;text-align:center}
.btn{width:100%;padding:11px;background:#4a90d9;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:500;cursor:pointer;transition:background .2s}
.btn:hover{background:#357abd}
.btn:disabled{background:#aaa;cursor:not-allowed}
.res{margin-top:20px;padding-top:18px;border-top:1px solid #eee}
.res audio{width:100%;margin-bottom:10px}
.res .dl{display:block;text-align:center;padding:10px;background:#34c759;color:#fff;border-radius:8px;text-decoration:none;font-weight:500;font-size:14px}
.res .dl:hover{background:#28a745}
.err{margin-top:14px;padding:10px;background:#ffe0e0;border-radius:8px;color:#c00;font-size:13px}
.load{text-align:center;margin-top:14px;color:#888;font-size:14px}
.hint{font-size:12px;color:#999;margin-top:3px}
.meta{background:#f8f9fa;border-radius:8px;padding:12px;margin-bottom:18px;display:none;font-size:13px}
.meta table{width:100%;border-collapse:collapse}
.meta td{padding:3px 6px}
.meta td:first-child{color:#888;width:100px;white-space:nowrap}
.meta td:last-child{font-weight:500;color:#333}
.badge{display:inline-block;background:#4a90d9;color:#fff;font-size:11px;border-radius:4px;padding:1px 6px;margin-left:4px}
.upload-area{border:2px dashed #d0d0d0;border-radius:8px;padding:30px;text-align:center;cursor:pointer;transition:border-color .2s;margin-bottom:16px}
.upload-area:hover,.upload-area.dragover{border-color:#4a90d9}
.upload-area p{color:#999;font-size:14px;margin-top:6px}
.upload-area .icon{font-size:36px;color:#bbb}
.controls{display:none;border:2px dashed transparent;border-radius:8px;padding:4px;transition:border-color .2s}
.presets{display:flex;gap:4px;flex-wrap:wrap;margin-top:5px}
.presets button{padding:2px 10px;font-size:11px;border:1px solid #ccc;border-radius:4px;background:#f8f8f8;cursor:pointer;color:#555;transition:all .15s}
.presets button:hover{background:#4a90d9;color:#fff;border-color:#4a90d9}
</style>
</head>
<body>
<div class=container>
<h1>Helium</h1>
<p class=sub>Helium &#26159;&#19968;&#20010;&#38899;&#39057;&#21464;&#36895;&#21464;&#35843;&#24037;&#20855;&#65292;&#22522;&#20110; FFmpeg rubberband &#28388;&#27874;&#23454;&#29616;&#39640;&#36136;&#37327;&#29420;&#31435;&#35843;&#25972;</p>

<div class=upload-area id=dropZone>
<div class=icon>&#128196;</div>
<p>&#28857;&#20987;&#25110;&#25302;&#21160;&#38899;&#39057;&#25991;&#20214;&#21040;&#27492;&#22788;</p>
<p style="font-size:12px;color:#bbb">MP3 / WAV / FLAC / OGG / M4A / AAC / OPUS / WMA</p>
</div>
<input type=file id=fileInput accept=".mp3,.wav,.flac,.ogg,.m4a,.aac,.wma,.opus" style="display:none">

<div class=meta id=metaBox><table><tbody id=metaBody></tbody></table></div>

<div class=controls id=controls>
<div class=grp>
<label>&#36895;&#24230;: <span id=sv>1.00</span>x</label>
<div class=row>
<input type=range min=0.25 max=4.0 step=0.05 value=1.0 id=spdSlider>
<input type=text id=spdText value="1.00">
</div>
<div class=hint>&#28369;&#22359; 0.25 ~ 4.0 &#65292;&#25991;&#26412; 0.1 ~ 10.0</div>
<div class=presets id=spdPresets></div>
</div>
<div class=grp>
<label>&#38899;&#39640;: <span id=pv>+0.0</span>st (<span id=pfv>1.000</span>x)</label>
<div class=row>
<input type=range min=-24 max=24 step=1 value=0 id=pitchSlider>
<input type=text id=pitchText value="1.000">
</div>
<div class=hint>&#28369;&#22359; -24 ~ +24 &#21322;&#38899; &#65292;&#25903;&#25345; 0.25 ~ 4.0 &#20493;&#29575;</div>
<div class=presets id=pitchPresets></div>
</div>
<div style="display:flex;gap:8px">
<button class=btn id=procBtn style="flex:1">&#24320;&#22987;&#22788;&#29702;</button>
<button class=btn style="flex:0;background:#888;padding:11px 14px;white-space:nowrap;font-size:13px" id=changeBtn>&#25442;&#25991;&#20214;</button>
</div>
<div class=hint style="text-align:center;margin-top:8px">&#20063;&#21487;&#25302;&#21160;&#26032;&#25991;&#20214;&#21040;&#27492;&#21306;&#22495;&#35206;&#30422;</div>
</div>

<div id=load class=load style=display:none>&#9200; &#22788;&#29702;&#20013;&#65292;&#35831;&#31561;&#24453;...</div>
<div id=res></div>
</div>

<script>
let fileId = null;

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); if(e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if(fileInput.files.length) handleFile(fileInput.files[0]); });

function handleFile(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!{{exts|safe}}.includes(ext)) { alert('Unsupported format'); return; }
  document.getElementById('res').innerHTML = '';
  document.getElementById('controls').style.display = 'none';
  document.getElementById('metaBox').style.display = 'none';
  document.getElementById('load').style.display = 'block';
  document.getElementById('load').textContent = '\u{1F4E4} Analyzing...';
  const fd = new FormData();
  fd.append('audio', file);
  fetch('/analyze', { method: 'POST', body: fd })
    .then(r => r.json())
    .then(d => {
      document.getElementById('load').style.display = 'none';
      if (d.error) { document.getElementById('res').innerHTML = '<div class=err>' + d.error + '</div>'; return; }
      fileId = d.id;
      const meta = d.meta;
      const rows = [
        ['Filename', meta.filename],
        ['Format', meta.format],
        ['Sample Rate', meta.sample_rate + ' Hz'],
        ['Channels', meta.channels == 1 ? 'Mono' : meta.channels == 2 ? 'Stereo' : meta.channels + ' channels'],
        ['Duration', meta.duration],
        ['Bit Rate', meta.bit_rate]
      ];
      document.getElementById('metaBody').innerHTML = rows.map(r => '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>').join('');
      document.getElementById('metaBox').style.display = 'block';
      document.getElementById('controls').style.display = 'block';
      dropZone.style.display = 'none';
    })
    .catch(e => { document.getElementById('load').style.display = 'none'; document.getElementById('res').innerHTML = '<div class=err>Upload failed: ' + e.message + '</div>'; });
}

const spdSlider = document.getElementById('spdSlider');
const spdText = document.getElementById('spdText');
const pitchSlider = document.getElementById('pitchSlider');
const pitchText = document.getElementById('pitchText');
const sv = document.getElementById('sv');
const pv = document.getElementById('pv');
const pfv = document.getElementById('pfv');

function semitoneToRatio(st) { return Math.pow(2, st / 12); }
function ratioToSemitone(r) { return 12 * Math.log2(r); }

function setSpeed(v) {
  v = Math.max(0.1, Math.min(10.0, v));
  spdText.value = v.toFixed(2);
  sv.textContent = spdText.value;
  if (v >= 0.25 && v <= 4.0) spdSlider.value = v;
}
function setPitchBySemitone(st) {
  st = Math.max(-24, Math.min(24, st));
  pitchSlider.value = st;
  const ratio = semitoneToRatio(st);
  pitchText.value = ratio.toFixed(3);
  pv.textContent = (st >= 0 ? '+' : '') + st.toFixed(1);
  pfv.textContent = ratio.toFixed(3);
}
function setPitchByRatio(v) {
  v = Math.max(0.25, Math.min(4.0, v));
  pitchText.value = v.toFixed(3);
  const st = ratioToSemitone(v);
  pfv.textContent = v.toFixed(3);
  pv.textContent = (st >= 0 ? '+' : '') + st.toFixed(1);
  if (st >= -24 && st <= 24) pitchSlider.value = st;
}

spdSlider.addEventListener('input', () => {
  spdText.value = parseFloat(spdSlider.value).toFixed(2);
  sv.textContent = spdText.value;
});
spdText.addEventListener('change', () => {
  let v = parseFloat(spdText.value);
  if (isNaN(v) || v < 0.1) v = 0.1;
  if (v > 10.0) v = 10.0;
  setSpeed(v);
});

pitchSlider.addEventListener('input', () => {
  const st = parseFloat(pitchSlider.value);
  const ratio = semitoneToRatio(st);
  pitchText.value = ratio.toFixed(3);
  pv.textContent = (st >= 0 ? '+' : '') + st.toFixed(1);
  pfv.textContent = ratio.toFixed(3);
});
pitchText.addEventListener('change', () => {
  let v = parseFloat(pitchText.value);
  if (isNaN(v) || v < 0.25) v = 0.25;
  if (v > 4.0) v = 4.0;
  setPitchByRatio(v);
});

// Build preset buttons
[0.5,0.75,1.0,1.25,1.5,2.0,3.0].forEach(function(v) {
  var b = document.createElement('button');
  b.textContent = v + 'x';
  b.addEventListener('click', function() { setSpeed(v); });
  document.getElementById('spdPresets').appendChild(b);
});
[-12,-6,-3,-1,0,1,3,6,12].forEach(function(st) {
  var b = document.createElement('button');
  b.textContent = (st > 0 ? '+' : '') + st + 'st';
  b.addEventListener('click', function() { setPitchBySemitone(st); });
  document.getElementById('pitchPresets').appendChild(b);
});

function showResult(d) {
  var t = Date.now();
  document.getElementById('res').innerHTML = '<div class=res><audio controls autoplay><source src="' + d.url + '?t=' + t + '" type="' + d.mime + '"></audio><a class=dl href="' + d.url + '" download="' + d.name + '">&#8681; Download</a></div>';
}

document.getElementById('procBtn').addEventListener('click', function() {
  if (!fileId) return;
  var btn = document.getElementById('procBtn');
  btn.disabled = true;
  document.getElementById('load').style.display = 'block';
  document.getElementById('load').textContent = '\u{1F50A} Processing...';
  document.getElementById('res').innerHTML = '';
  fetch('/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: fileId,
      speed: parseFloat(spdText.value) || 1.0,
      pitch: parseFloat(pitchText.value) || 1.0
    })
  })
    .then(r => r.json())
    .then(function(d) {
      document.getElementById('load').style.display = 'none';
      if (d.error) { document.getElementById('res').innerHTML = '<div class=err>' + d.error + '</div>'; return; }
      showResult(d);
    })
    .catch(function(e) { document.getElementById('load').style.display = 'none'; document.getElementById('res').innerHTML = '<div class=err>Process failed: ' + e.message + '</div>'; })
    .finally(function() { btn.disabled = false; });
});

// Change file
document.getElementById('changeBtn').addEventListener('click', function() { fileInput.click(); });

// Allow drag-drop onto controls area to replace
var controls = document.getElementById('controls');
controls.addEventListener('dragover', function(e) { e.preventDefault(); controls.style.borderColor = '#4a90d9'; });
controls.addEventListener('dragleave', function() { controls.style.borderColor = ''; });
controls.addEventListener('drop', function(e) {
  e.preventDefault();
  controls.style.borderColor = '';
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
</script>
</body>
</html>'''

def ffmpeg_cmd():
    return [FFMPEG]

def ffprobe_cmd():
    return [FFPROBE]

def get_audio_meta(fp):
    cmd = ffprobe_cmd() + ['-v', 'quiet', '-print_format', 'json',
                           '-show_format', '-show_streams', str(fp)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'ffprobe error: {r.stderr}')
    data = json.loads(r.stdout)
    streams = data.get('streams', [])
    fmt = data.get('format', {})
    info = {'filename': Path(fp).name}
    for s in streams:
        if s.get('codec_type') == 'audio':
            info['sample_rate'] = s.get('sample_rate', '?')
            info['channels'] = s.get('channels', '?')
            info['codec'] = s.get('codec_name', '?')
            break
    dur = float(fmt.get('duration', 0))
    h, m = int(dur // 3600), int((dur % 3600) // 60)
    s = dur % 60
    info['duration'] = f'{h:02d}:{m:02d}:{s:05.2f}' if h else f'{m:02d}:{s:05.2f}'
    info['bit_rate'] = fmt.get('bit_rate', '?')
    if info['bit_rate'] != '?':
        info['bit_rate'] = f"{int(info['bit_rate']) // 1000} kbps"
    info['format'] = fmt.get('format_name', '?')
    return info


def atempo_chain(ratio):
    parts = []
    while ratio > 2.0:
        parts.append('atempo=2.0')
        ratio /= 2.0
    while ratio < 0.5:
        parts.append('atempo=0.5')
        ratio /= 0.5
    if abs(ratio - 1.0) > 0.001:
        parts.append(f'atempo={ratio:.6f}')
    return ','.join(parts)


def mime_type(ext):
    return {'.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.flac': 'audio/flac',
            '.ogg': 'audio/ogg', '.m4a': 'audio/mp4', '.aac': 'audio/aac',
            '.opus': 'audio/opus'}.get(ext, 'application/octet-stream')


def output_codec(ext):
    return {'.mp3': 'libmp3lame', '.m4a': 'aac', '.aac': 'aac',
            '.ogg': 'libvorbis', '.opus': 'libopus', '.wma': 'wmav2',
            '.flac': 'flac'}.get(ext, 'libmp3lame')


def process(inp, out, speed_ratio, pitch_ratio):
    sr = get_sample_rate(inp)
    # Use librubberband for high-quality independent tempo & pitch control
    filter_str = f'rubberband=tempo={speed_ratio:.4f}:pitch={pitch_ratio:.4f}:transients=crisp'
    ext = Path(out).suffix.lower()
    cmd = ffmpeg_cmd() + ['-y', '-i', str(inp), '-af', filter_str,
                          '-ar', str(sr), '-c:a', output_codec(ext)]
    if ext == '.mp3':
        cmd += ['-q:a', '2']
    elif ext in ('.m4a', '.aac'):
        cmd += ['-b:a', '192k']
    cmd.append(str(out))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:] if len(r.stderr) > 2000 else r.stderr)


def get_sample_rate(fp):
    cmd = ffprobe_cmd() + ['-v', 'error', '-show_entries', 'stream=sample_rate',
                           '-of', 'default=noprint_wrappers=1:nokey=1', str(fp)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'ffprobe error: {r.stderr}')
    return int(r.stdout.strip().split('\n')[0])


def cleanup():
    now = time.time()
    for d in (UPLOAD_DIR, PROCESSED_DIR):
        for f in d.iterdir():
            if f.is_file() and now - f.stat().st_mtime > 7200:
                f.unlink(missing_ok=True)


@app.route('/')
def index():
    exts = '["' + '","'.join(SUPPORTED_EXTS) + '"]'
    return render_template_string(HTML, exts=exts)


@app.route('/analyze', methods=['POST'])
def analyze():
    cleanup()
    if 'audio' not in request.files:
        return jsonify(error='No file uploaded'), 400
    f = request.files['audio']
    if not f.filename:
        return jsonify(error='Empty filename'), 400
    ext = Path(f.filename).suffix.lower()
    if ext not in SUPPORTED_EXTS:
        return jsonify(error=f'Unsupported format: {ext}'), 400
    uid = uuid.uuid4().hex
    in_path = UPLOAD_DIR / f'{uid}{ext}'
    f.save(str(in_path))
    try:
        meta = get_audio_meta(in_path)
        return jsonify(id=uid, meta=meta)
    except Exception as e:
        in_path.unlink(missing_ok=True)
        return jsonify(error=str(e)), 500


@app.route('/process', methods=['POST'])
def process_route():
    cleanup()
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify(error='Missing id'), 400
    uid = data['id']
    speed = float(data.get('speed', 1.0))
    pitch = float(data.get('pitch', 1.0))
    speed = max(0.1, min(10.0, speed))
    pitch = max(0.25, min(4.0, pitch))
    in_path = None
    for f in UPLOAD_DIR.iterdir():
        if f.stem == uid and f.suffix.lower() in SUPPORTED_EXTS:
            in_path = f
            break
    if not in_path:
        return jsonify(error='File not found (expired?)'), 404
    ext = in_path.suffix.lower()
    out_path = PROCESSED_DIR / f'{uid}{ext}'
    try:
        process(in_path, out_path, speed, pitch)
        return jsonify(url=f'/processed/{uid}{ext}', mime=mime_type(ext),
                       name=f'processed_{speed:.2f}x_{pitch:.3f}x{ext}')
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/processed/<name>')
def serve(name):
    p = PROCESSED_DIR / name
    if not p.is_file():
        return 'Not found', 404
    return send_file(str(p), mimetype=mime_type(Path(name).suffix.lower()))


if __name__ == '__main__':
    if not os.path.isfile(FFMPEG):
        print(f'ERROR: ffmpeg not found at {FFMPEG}')
        input('Press Enter to exit...')
        exit(1)
    if not os.path.isfile(FFPROBE):
        print(f'ERROR: ffprobe not found at {FFPROBE}')
        input('Press Enter to exit...')
        exit(1)
    url = 'http://127.0.0.1:5566'
    print(f' * Running on {url}')
    print(' * Press Ctrl+C to stop')
    webbrowser.open(url)
    try:
        app.run(host='127.0.0.1', port=5566, debug=False)
    except KeyboardInterrupt:
        print('\nShutting down gracefully...')
        cleanup()
        print('Done.')
