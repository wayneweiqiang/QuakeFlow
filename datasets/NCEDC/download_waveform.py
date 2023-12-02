# %%
import multiprocessing as mp
import os
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import obspy
import pandas as pd
from tqdm.auto import tqdm
from glob import glob

matplotlib.use("Agg")

warnings.filterwarnings("ignore")

os.environ["OPENBLAS_NUM_THREADS"] = "2"

# %%
root_path = "./"
catalog_path = f"dataset/catalog"
station_path = f"{root_path}/station"
waveform_path = f"{root_path}/waveform/"
dataset_path = f"dataset"
if not os.path.exists(dataset_path):
    os.makedirs(dataset_path)

# %%
def cut_data(event, phases):
    arrival_time = phases.loc[event.event_id, "phase_time"].min()
    begin_time = arrival_time - pd.Timedelta(seconds=35)
    end_time = arrival_time + pd.Timedelta(seconds=95)

    for _, pick in phases.loc[event.event_id].iterrows():
        # outfile_path = (
        #     dataset_path
        #     / "waveform"
        #     / f"{event.time.year}"
        #     / f"{event.time.year}.{event.time.dayofyear:03d}"
        #     / f"{event.event_id}"
        # )
        outfile_path = f"{dataset_path}/waveform/{event.time.year}/{event.time.year}.{event.time.dayofyear:03d}/{event.event_id}"

        # if (outfile_path / f"{pick.network}.{pick.station}.{pick.location}.{pick.instrument}.mseed").exists():
        #     continue
        # if os.path.exists(f"{outfile_path}/{pick.network}.{pick.station}.{pick.location}.{pick.instrument}.mseed"):
        #     continue

        # inv_path = (
        #     station_path / f"{pick.network}.info" / f"{pick.network}.FDSN.xml" / f"{pick.network}.{pick.station}.xml"
        # )
        # if not inv_path.exists():
        #     continue
        inv_path = f"{station_path}/{pick.network}.info/{pick.network}.FDSN.xml/{pick.network}.{pick.station}.xml"
        if not os.path.exists(inv_path):
            continue
        inv = obspy.read_inventory(str(inv_path))

        # begin_mseed_path = (
        #     waveform_path
        #     / f"{pick.network}"
        #     / f"{begin_time.year}"
        #     / f"{begin_time.year}.{begin_time.dayofyear:03d}"
        #     / f"{pick.station}.{pick.network}.{pick.instrument}?.{pick.location}.?.{begin_time.year}.{begin_time.dayofyear:03d}"
        # )
        # end_mseed_path = (
        #     waveform_path
        #     / f"{pick.network}"
        #     / f"{end_time.year}"
        #     / f"{end_time.year}.{end_time.dayofyear:03d}"
        #     / f"{pick.station}.{pick.network}.{pick.instrument}?.{pick.location}.?.{end_time.year}.{end_time.dayofyear:03d}"
        # )
        begin_mseed_path = f"{waveform_path}/{pick.network}/{begin_time.year}/{begin_time.year}.{begin_time.dayofyear:03d}/{pick.station}.{pick.network}.{pick.instrument}?.{pick.location}.?.{begin_time.year}.{begin_time.dayofyear:03d}"
        end_mseed_path = f"{waveform_path}/{pick.network}/{end_time.year}/{end_time.year}.{end_time.dayofyear:03d}/{pick.station}.{pick.network}.{pick.instrument}?.{pick.location}.?.{end_time.year}.{end_time.dayofyear:03d}"
        try:
            st = obspy.Stream()
            for mseed_path in set([begin_mseed_path, end_mseed_path]):
                st += obspy.read(str(mseed_path))
        except Exception as e:
            print(e)
            continue

        if len(st) == 0:
            # print(f"{event.event_id}.{pick.network}.{pick.station}.{pick.location}.{pick.instrument} is empty")
            continue

        try:
            st.merge(fill_value="latest")
            st.remove_sensitivity(inv)
            st.detrend("constant")
            st.trim(obspy.UTCDateTime(begin_time), obspy.UTCDateTime(end_time), pad=True, fill_value=0)
        except Exception as e:
            print(e)
            continue

        # if not outfile_path.exists():
        #     outfile_path.mkdir(parents=True)
        # st.write(
        #     outfile_path / f"{pick.network}.{pick.station}.{pick.location}.{pick.instrument}.mseed",
        #     format="MSEED",
        # )
        if not os.path.exists(outfile_path):
            os.makedirs(outfile_path)
        st.write(
            f"{outfile_path}/{pick.network}.{pick.station}.{pick.location}.{pick.instrument}.mseed",
            format="MSEED",
        )

        # outfile_path = (
        #     dataset_path
        #     / "figure"
        #     / f"{event.time.year}"
        #     / f"{event.time.year}.{event.time.dayofyear:03d}"
        #     / f"{event.event_id}"
        # )
        # if not outfile_path.exists():
        #     outfile_path.mkdir(parents=True)

        # st.plot(outfile=outfile_path / f"{pick.network}.{pick.station}.{pick.location}.{pick.instrument}.png")
        outfile_path = f"{dataset_path}/figure/{event.time.year}/{event.time.year}.{event.time.dayofyear:03d}/{event.event_id}"
        if not os.path.exists(outfile_path):
            os.makedirs(outfile_path)
        st.plot(outfile=f"{outfile_path}/{pick.network}.{pick.station}.{pick.location}.{pick.instrument}.png")

    return 0


# %%
if __name__ == "__main__":
    ncpu = 32
    # ncpu = 1
    # event_list = sorted(list(catalog_path.glob("*.event.csv")))[::-1]
    event_list = sorted(list(glob(f"{catalog_path}/*.event.csv")))[::-1]
    start_year = "1966"
    end_year = "2022"
    # end_year = "2014"
    tmp = []
    for event_file in event_list:
        # if event_file.name.split(".")[0] >= start_year and event_file.name.split(".")[0] <= end_year:
        #     tmp.append(event_file)
        if event_file.split("/")[-1].split(".")[0] >= start_year and event_file.split("/")[-1].split(".")[0] <= end_year:
            tmp.append(event_file)
    event_list = sorted(tmp)[::-1]

    # pool = mp.get_context("spawn").Pool(ncpu)
    for event_file in event_list:
        print(event_file)
        events = pd.read_csv(event_file, parse_dates=["time"])
        # phases = pd.read_csv(
        #     event_file.parent / (event_file.name.replace("event.csv", "phase.csv")),
        #     parse_dates=["phase_time"],
        #     keep_default_na=False,
        # )
        phases = pd.read_csv(
            f"{event_file.replace('event.csv', 'phase.csv')}",
            parse_dates=["phase_time"],
            keep_default_na=False,
        )
        phases = phases.loc[
            phases.groupby(["event_id", "network", "station", "location", "instrument"]).phase_time.idxmin()
        ]
        phases.set_index("event_id", inplace=True)

        events = events[events.event_id.isin(phases.index)]
        pbar = tqdm(events, total=len(events))
        with mp.get_context("spawn").Pool(ncpu) as p:
            for _, event in events.iterrows():
                p.apply_async(cut_data, args=(event, phases.loc[event.event_id]), callback=lambda _: pbar.update(1))
            p.close()
            p.join()
        pbar.close()

        # pool.starmap(cut_data, [(event, phases.loc[event.event_id]) for _, event in events.iterrows()])
    # pool.close()
