// proto_dump.js —— hook protobuf 序列化，抓取 App 收发数据里的 g1.* SKU
// 用法：frida -U -n "Google One" -l proto_dump.js --runtime=v8
// 或者用 run 脚本注入
Java.perform(function () {
  var TAG = "PD";
  var seen = {};

  function bytesToAscii(arr) {
    var out = "";
    for (var i = 0; i < arr.length; i++) {
      var b = arr[i] & 0xff;
      out += (b >= 32 && b < 127) ? String.fromCharCode(b) : ".";
    }
    return out;
  }

  function scan(arr, where) {
    try {
      var s = bytesToAscii(arr);
      var rx = /g1\.[A-Za-z0-9_.]{4,60}/g;
      var m, found = [];
      while ((m = rx.exec(s)) !== null) {
        if (found.indexOf(m[0]) < 0) found.push(m[0]);
      }
      if (!found.length) {
        // 也找 ultra / ai.pro 关键字
        if (s.indexOf("ultra") >= 0 || s.indexOf("Ultra") >= 0) {
          var i = s.toLowerCase().indexOf("ultra");
          console.log("[" + TAG + "][" + where + "] ..." + s.slice(Math.max(0, i - 60), i + 80) + "...");
        }
        return;
      }
      found.forEach(function (sku) {
        var k = where + "|" + sku;
        if (seen[k]) return;
        seen[k] = 1;
        console.log("[" + TAG + "][" + where + "] SKU " + sku);
      });
    } catch (e) {}
  }

  // 1) 出站：MessageLite.toByteArray()
  try {
    var ML = Java.use("com.google.protobuf.MessageLite");
    var GML = Java.use("com.google.protobuf.GeneratedMessageLite");
    GML.toByteArray.implementation = function () {
      var r = this.toByteArray();
      try { scan(r, "OUT:" + this.getClass().getSimpleName()); } catch (e) {}
      return r;
    };
    console.log("[" + TAG + "] hook toByteArray OK");
  } catch (e) {
    console.log("[" + TAG + "] toByteArray hook fail: " + e);
  }

  // 2) 入站：parseFrom(byte[]) / parseFrom(byte[], int, int)
  try {
    var GML2 = Java.use("com.google.protobuf.GeneratedMessageLite");
    var overloads = GML2.parseFrom.overloads;
    overloads.forEach(function (ov) {
      var args = ov.argumentTypes;
      if (args.length >= 1 && String(args[0].className) === "[B") {
        ov.implementation = function () {
          try {
            var arr = arguments[0];
            scan(arr, "IN:" + this.getClass().getSimpleName());
          } catch (e) {}
          return ov.apply(this, arguments);
        };
      }
    });
    console.log("[" + TAG + "] hook parseFrom OK (" + overloads.length + " overloads)");
  } catch (e) {
    console.log("[" + TAG + "] parseFrom hook fail: " + e);
  }

  console.log("[" + TAG + "] ready");
});
