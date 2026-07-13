import os
import json
from datetime import datetime
import pandas as pd

def safe_float(val):
    try:
        if pd.isna(val):
            return 0.0
        if isinstance(val, str):
            val = val.replace('%', '').replace(',', '').strip()
            if val.lower() in ['available', 'n/a', 'null', 'none', '-']:
                return 0.0
        return float(val)
    except:
        return 0.0

def safe_int(val):
    try:
        if pd.isna(val):
            return 0
        return int(float(val))
    except:
        return 0

def process_rvtools_workbook(file_path, customer_name, cluster_label):
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_map = {s.strip().lower(): s for s in excel_file.sheet_names}

        # --- 1. Pull core vmList tab data ---
        vmlist_tab = sheet_map.get('vmlist')
        if not vmlist_tab:
            return {"error": "Missing mandatory vmList / vMList tab layout configuration."}
        
        df_vm = pd.read_excel(file_path, sheet_name=vmlist_tab)
        
        # --- 2. Pull storage lookup matrices ---
        vdisk_tab = sheet_map.get('vdisk')
        vdisk_map = {}
        if vdisk_tab:
            df_disk = pd.read_excel(file_path, sheet_name=vdisk_tab)
            for _, row in df_disk.iterrows():
                vm_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
                if vm_name:
                    vdisk_map[vm_name] = vdisk_map.get(vm_name, 0.0) + safe_float(row.iloc[2])

        vpart_tab = sheet_map.get('vpartition')
        part_cfg_map = {}
        part_used_map = {}
        if vpart_tab:
            df_part = pd.read_excel(file_path, sheet_name=vpart_tab)
            for _, row in df_part.iterrows():
                vm_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
                if vm_name:
                    part_used_map[vm_name] = part_used_map.get(vm_name, 0.0) + safe_float(row.iloc[3])
                    part_cfg_map[vm_name] = part_cfg_map.get(vm_name, 0.0) + safe_float(row.iloc[4])

        # --- 3. Pull separate vCPU performance data based on absolute layout indexes ---
        vcpu_tab = sheet_map.get('vcpu')
        vcpu_map = {}
        if vcpu_tab:
            df_cpu = pd.read_excel(file_path, sheet_name=vcpu_tab)
            for _, row in df_cpu.iterrows():
                vm_name = str(row.iloc[0]).strip()
                if pd.notna(vm_name):
                    vcpu_map[vm_name] = {
                        "peak": safe_float(row.iloc[5]),
                        "avg": safe_float(row.iloc[6]),
                        "cpu95th": safe_float(row.iloc[8])
                    }

        # --- 4. Pull environmental tracking tabs ---
        dc_count = len(pd.read_excel(file_path, sheet_name=sheet_map.get('vdatacenter'))) if sheet_map.get('vdatacenter') else 1
        cluster_count = len(pd.read_excel(file_path, sheet_name=sheet_map.get('vcluster'))) if sheet_map.get('vcluster') else 1
        
        host_list = []
        host_tab = sheet_map.get('vhosts') or sheet_map.get('vhost')
        if host_tab:
            df_host = pd.read_excel(file_path, sheet_name=host_tab)
            cols = {c.lower().replace(" ", ""): i for i, c in enumerate(df_host.columns)}
            
            h_idx = cols.get('host') or cols.get('hostname') or cols.get('hostip') or 0
            m_idx = cols.get('model') or cols.get('hardwaremodel') or 1
            cm_idx = cols.get('cpumodel') or cols.get('processortype') or 2
            speed_idx = cols.get('cpuspeedghz') or cols.get('cpuspeed') or cols.get('speed') or 3
            mem_idx = cols.get('memorysize') or cols.get('memorysizemib') or cols.get('ram') or 4

            for _, r in df_host.iterrows():
                raw_speed = safe_float(r.iloc[speed_idx])
                final_speed = raw_speed / 1000 if raw_speed > 100 else raw_speed
                
                raw_mem = safe_float(r.iloc[mem_idx])
                final_mem = raw_mem / 1024 if raw_mem > 4096 else raw_mem

                host_list.append({
                    "Host Name": str(r.iloc[h_idx]) if pd.notna(r.iloc[h_idx]) else "Unknown Node",
                    "Model": str(r.iloc[m_idx]) if pd.notna(r.iloc[m_idx]) else "-",
                    "CPU Model": str(r.iloc[cm_idx]) if pd.notna(r.iloc[cm_idx]) else "-",
                    "CPU Speed (GHz)": final_speed,
                    "Memory Size": final_mem
                })

        snap_list = []
        snap_tab = sheet_map.get('vsnapshot')
        if snap_tab:
            df_snap = pd.read_excel(file_path, sheet_name=snap_tab)
            for _, r in df_snap.iloc[:40].iterrows():
                snap_list.append({
                    "VM Name": str(r.iloc[0]) if pd.notna(r.iloc[0]) else "Unknown",
                    "Snapshot Name": str(r.iloc[1]) if pd.notna(r.iloc[1]) else "Unnamed",
                    "Size MiB (total)": safe_float(r.iloc[2])
                })

        # --- 5. Consolidate VM list rollup maps ---
        vm_rollup = []
        for _, row in df_vm.iterrows():
            name = str(row.iloc[0]).strip()
            if not name or pd.isna(row.iloc[0]):
                continue
            
            ram_mib = safe_float(row.iloc[5])
            cpu_profile = vcpu_map.get(name, {"cpu95th": 0.0, "peak": 0.0, "avg": 0.0})

            vm_rollup.append({
                "name": name,
                "state": str(row.iloc[2]) if pd.notna(row.iloc[2]) else "Unknown",
                "vcpus": safe_int(row.iloc[3]),
                "ramGB": ram_mib / 1024,
                "vdiskCapMiB": safe_float(vdisk_map.get(name, row.iloc[7] if pd.notna(row.iloc[7]) else 0.0)),
                "cpu95th": cpu_profile["cpu95th"],
                "cpuPeak": cpu_profile["peak"],
                "cpuAvg": cpu_profile["avg"],
                "partitionConfigMiB": safe_float(part_cfg_map.get(name, 0.0)),
                "partitionConsumedMiB": safe_float(part_used_map.get(name, 0.0)),
                "os": str(row.iloc[15]) if len(row) > 15 and pd.notna(row.iloc[15]) else "Other"
            })

        payload = {
            "kpis": {"dc": dc_count, "clusters": cluster_count, "hosts": len(host_list), "gpus": 0},
            "cache": {"vmRollup": vm_rollup},
            "raw": {"clusters": [], "snaps": snap_list, "hosts": host_list}
        }

        customer_dir = os.path.join('customers', customer_name.replace(' ', '_'))
        os.makedirs(customer_dir, exist_ok=True)
        
        date_stamp = datetime.now().strftime("%m.%d.%y")
        output_file_name = f"{cluster_label.replace(' ', '_')}_{date_stamp}.json"
        output_path = os.path.join(customer_dir, output_file_name)

        with open(output_path, 'w') as f:
            json.dump(payload, f, indent=2)

        print(f"✅ Successfully compiled: {output_path}")
        return {"status": "success", "file": output_file_name}

    except Exception as e:
        print(f"❌ Error processing: {str(e)}")
        return {"error": str(e)}