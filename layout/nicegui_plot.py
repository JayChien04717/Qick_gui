import asyncio
import numpy as np
from typing import Callable, Optional, Any
from tqdm.auto import tqdm
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from qick_workspace.tools import fitting as fitter

async def nicegui_plot(
    prog: Any,
    soc: Any,
    py_avg: int,
    plot_callback: Callable[[np.ndarray, int], None],
    progress_callback: Optional[Callable[[int, int, Optional[float]], None]] = None,
    is_running_callback: Optional[Callable[[], bool]] = None,
) -> tuple[np.ndarray, bool]:
    """
    Executes a QICK program with software averaging and live plotting updates for NiceGUI.

    Args:
        prog: The QICK program instance.
        soc: The QICK SoC instance.
        py_avg: Number of software averages.
        plot_callback: Function called with (current_data, current_avg_count).
                       current_data is a 1D numpy array of magnitudes.
        progress_callback: Optional function called with (current_avg, total_avg, remaining_time).
                           remaining_time is in seconds (or None if unknown).
        is_running_callback: Optional function that returns False to stop the measurement.

    Returns:
        tuple: (final_iq_data, interrupted)
               final_iq_data is the complex IQ data (averaged).
               interrupted is True if the measurement was stopped early.
    """
    iq_sum = None
    interrupted = False
    
    # Pre-allocate if possible or just handle first iteration
    
    with tqdm(total=py_avg, desc="Averaging") as pbar:
        for i in range(py_avg):
            # Check if we should stop
            if is_running_callback and not is_running_callback():
                interrupted = True
                break

            # Acquire 1 round of data
            # Use asyncio.to_thread to keep the UI responsive
            # progress=False because we handle progress manually
            iq_list = await asyncio.to_thread(prog.acquire, soc, rounds=1, progress=False)
            
            # Extract data: iq_list[0][0] is usually the buffer for the first readout
            # dot([1, 1j]) converts I, Q to complex
            iq_data = iq_list[0][0].dot([1, 1j])
            
            if iq_sum is None:
                iq_sum = iq_data
            else:
                iq_sum += iq_data
                
            # Calculate current average
            current_avg_data = iq_sum / (i + 1)
            
            # Update plot
            # We pass the magnitude for plotting
            plot_callback(np.abs(current_avg_data), i + 1)
            
            # Update progress
            pbar.update(1)
            if progress_callback:
                # Get remaining time from tqdm
                # format_dict['elapsed'] is time spent
                # rate is it/s
                # remaining = (total - n) / rate
                remaining = None
                if pbar.format_dict['rate'] and pbar.format_dict['rate'] > 0:
                    remaining = (pbar.total - pbar.n) / pbar.format_dict['rate']
                
                progress_callback(i + 1, py_avg, remaining)
                
            # Small sleep to allow UI updates to propagate if needed
            # (NiceGUI/FastAPI handles this mostly via await, but a tiny sleep can help yield control)
            await asyncio.sleep(0.001)

    if iq_sum is None:
        return None, True

    final_data = iq_sum / (i + 1) if not interrupted else iq_sum / (i + 1)
    return final_data, interrupted



def nicegui_plot_final(xpts, data: np.ndarray, x_label: str, fitfunc, simfunc, return_ax=False, fig=None, title=None):
    """
    Generates a comprehensive plot with fitting results for NiceGUI.
    Based on the user's provided plot_final function.
    """
    marker_style = {
        "marker": "o",
        "markersize": 5,
        "alpha": 0.7,
        "linestyle": "-",
    }

    data_dict = {
        "xpts": xpts,
        "amps": np.abs(data),
        "phase": np.unwrap(np.angle(data)),
        "avgi": data.real,
        "avgq": data.imag,
    }

    for measure in ("amps", "phase", "avgi", "avgq"):
        try:
            popt, pcov, f = fitfunc(data_dict["xpts"], data_dict[measure])
            data_dict[f"fit_{measure}"] = popt
            data_dict[f"fit_err_{measure}"] = pcov
        except Exception as e:
            print(f"Fit failed for {measure}: {e}")

    try:
        fit_params, fit_err, best_measure = fitter.get_best_fit(data_dict, fitfunc=None)
    except Exception as e:
        print(f"Get best fit failed: {e}")
        # Fallback if get_best_fit fails
        best_measure = "amps"
        fit_params = data_dict.get(f"fit_{best_measure}", [])
        fit_err = data_dict.get(f"fit_err_{best_measure}", [])

    # Create figure using pyplot directly, NiceGUI will capture it if used inside ui.matplotlib context
    # OR we return the figure and let the caller handle it.
    # The user snippet creates a figure: fig = plt.figure(figsize=(12, 6))
    # We should probably return the figure so it can be used in ui.matplotlib(figure=fig) or similar.
    
    if fig is None:
        fig = plt.figure(figsize=(12, 6))
    else:
        fig.clf() # Clear existing figure content if reusing
    
    if title:
        fig.suptitle(title)
        
    gs = gridspec.GridSpec(2, 3, width_ratios=[1, 1, 2])

    measures = ("amps", "phase", "avgi", "avgq")
    for i, measure in enumerate(measures):
        row = i // 2
        col = i % 2
        ax = fig.add_subplot(gs[row, col])
        ax.plot(data_dict["xpts"], data_dict[measure], **marker_style)
        ax.set_xlabel(x_label)
        ax.set_ylabel(f"{measure} (ADC unit)")
        if f"fit_{measure}" in data_dict:
            try:
                ax.plot(
                    data_dict["xpts"],
                    simfunc(data_dict["xpts"], *data_dict[f"fit_{measure}"]),
                )
            except Exception:
                pass
        ax.set_title(measure)

    ax_big = fig.add_subplot(gs[:, 2])
    ax_big.set_title(f"Best fit: {best_measure}")
    ax_big.plot(data_dict["xpts"], data_dict[best_measure], **marker_style)
    try:
        ax_big.plot(data_dict["xpts"], simfunc(data_dict["xpts"], *fit_params))
    except Exception:
        pass
    ax_big.set_xlabel(x_label)
    ax_big.set_ylabel("ADC unit")
    
    fig.tight_layout()

    error = np.sqrt(np.diag(fit_err)) if len(fit_err) > 0 else []
    
    if return_ax:
        return fit_params, error, fig, ax_big
    else:
        return fit_params, error, fig
