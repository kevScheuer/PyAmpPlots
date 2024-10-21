/* Extract the fit results from a list of AmpTools output files and writes them to a csv
The csv file will have the following columns:
    - eMatrixStatus
    - lastMinuitCommandStatus
    - likelihood
    - detected_events
    - detected_events_err
    - generated_events
    - generated_events_err
    - AmpTools parameters
    - all amplitude coherent sums
    - all phase differences

This script assumes the amplitudes are named in the vector-pseudoscalar style 'eJPmL'
format, where:
    e = reflectivity (either p [+] or m [-])
    J = total spin (positive integers including 0)
    P = parity (either p [+] or m [-])
    m = m-projection (either p [+], m [-], or 0)
    L = orbital angular momentum (standard letter convention: S, P, D, F, ...)
It also assumes that reflectivity sums do not mix, meaning that phase differences can
not be computed between negative and positive reflectivity waves.


NOTE: this script is "reaction" independent, meaning if multiple reactions are in the
    fit, it assumes the phase differences are common across all of them. It also means
    that coherent sums are calculated over all reactions. This is so that multiple
    orientations, typically denoted using the "reaction", can be fit simultaneously and
    have their fit results extracted in one go.
*/

#include <cstring>
#include <fstream> // for writing csv
#include <iostream>
#include <map>
#include <sstream> // for std::istringstream
#include <string>
#include <vector>

#include "IUAmpTools/FitResults.h"
#include "TMath.h"

// forward declarations
void fill_maps(
    FitResults &results,
    std::map<std::string, double> &standard_results,
    std::map<std::string, std::pair<std::string, std::string>> &phase_diffs,
    std::map<std::string, std::map<std::string, std::vector<std::string>>> &coherent_sums);

std::tuple<std::string, std::string, std::string, std::string> parse_amplitude(std::string amplitude);

void extract_fit_results(std::string files, std::string csv_name, bool is_acceptance_corrected)
{

    // store space-separated list of files into a vector
    std::vector<std::string> file_vector;
    std::istringstream iss(files);
    std::string file;
    while (iss >> file)
    {
        file_vector.push_back(file);
    }

    // ==== MAP INITIALIZATION ====

    // map of the standard AmpTools outputs that will be common to any fit result
    std::map<std::string, double> standard_results;

    // map for all phase differences between amplitudes, whose keys are in
    // "eJPmL_eJPmL" format, and whose values are the pair of full AmpTools
    // amplitude names
    std::map<std::string, std::pair<std::string, std::string>> phase_diffs;

    // This next map stores all the different coherent sum types. The keys are the
    // coherent sum type in eJPmL format, and the values are the strings of each
    // amplitude in that type. These strings are mapped to a vector of amplitudes
    // which are the full AmpTools names of the amplitudes that match that coherent sum.
    // Any quantum numbers that are dropped from the key means they have been coherently
    // summed over.

    // EXAMPLES
    // An individual amplitude such as the positive reflectivity, JP=1+, S-wave with a
    // +1 m-projection is then stored like:
    // "eJPmL -> "p1p0S" -> {xx::ImagPosSign::p1p0S, xx::RealNegSign::p1p0S}
    // An example of a coherent sum such as the over all JP=1+ states would be:
    // "JP" -> "1p" -> {xx::ImagNegSign::m1p0S, xx::RealNegSign::p1ppD, ...}

    // Initialize the map for all coherent sum types
    std::map<std::string, std::map<std::string, std::vector<std::string>>> coherent_sums;
    std::vector<std::string> coherent_sum_types = {
        "eJPmL",    // single amplitudes
        "JPmL",     // sum reflectivity
        "eJPL",     // sum m-projection
        "JPL",      // sum {reflectivity, m-projection}
        "eJP",      // sum {m-projection, angular momenta}
        "JP",       // sum {reflectivity, m-projection, angular momenta
        "e"         // sum all except reflectivity
    } for (const auto &key : coherent_sum_types)
    {
        coherent_sums[key] = std::map<std::string, std::vector<std::string>>();
    }

    // finally a map for the production coefficients (in eJPmL format) and their errors
    std::map<std::string, std::complex<double, double>> production_coefficients;

    // open csv file for writing
    std::ofstream csv_file;
    csv_file.open(csv_name);

    // ==== BEGIN FILE ITERATION ====
    // Iterate over each file, and add their results as a row in the csv
    for (std::string file : file_vector)
    {
        cout << "Analyzing File: " << file << "\n";
        FitResults results(file);
        if (!results.valid())
        {
            cout << "Invalid fit results in file: " << file << "\n";
            continue;
        }

        // before getting this file's info, clear the results from the last file
        standard_results.clear();
        production_coefficients.clear();
        for (const auto& [key, val] : coherent_sums)
        {
            val.clear();
        }
        phase_diffs.clear();
        
        // fill all the maps for this file
        fill_maps(results, standard_results, production_coefficients, coherent_sums, phase_diffs);

        // == WRITE TO CSV ==
        // write the header row if this is the first file
        if (csv_file.tellp() == 0)
        {
            // 1. standard results (these already have _err values)
            for (const auto& [kev, val] : standard_results)
            {
                csv_file << key << ",";
            }
            // 2. AmpTools parameter names
            for (const auto& par_name : results.parNameList())
            {                
                // skip amplitude-based parameters
                if (par_name.find("::") != std::string::npos)
                {
                    continue;
                }
                csv_file << par_name << "," << par_name << "_err,";
            }
            // 3. production parameters in eJPmL_(re/im) format
            for (const auto& [key, complex_val] : production_coefficients)
            {
                csv_file << key << "_re" << ",";
                csv_file << key << "_im" << ",";
            }
            // 4. eJPmL based coherent sum titles
            for (const auto& [sum_name, sum_map] : coherent_sums)
            {
                for (const auto& [sum, amp_vector] : coherent_sums[sum_name])
                {
                    csv_file << sum << "," << sum << "_err,";
                }
            }
            // 5. phase difference names in eJPmL_eJPmL format
            for (const auto& [pd_name, pd_pair] : phase_diffs)
            {
                csv_file << pd_name << "," << pd_name << "_err,";
            }
            csv_file << "\n";
        } // end header row

        // now write the values in the same oder of map loops
        // 1. standard results
        for (const auto& [key, val] : standard_results)
        {
            csv_file << val << ",";
        }
        // 2. AmpTools parameters
        for (const auto& par_name : results.parNameList())
        {
            // skip amplitude-based parameters
            if (par_name.find("::") != std::string::npos)
            {
                continue;
            }
            csv_file << results.parValue(par_name) << ",";
            csv_file << results.parError(par_name) << ",";          
        }
        // 3. production parameters
        for (const auto& [key, complex_val] : production_coefficients)
        {
            csv_file << complex_val.real() << ",";
            csv_file << complex_val.imag() << ",";
        }
        // 4. coherent sums
        for (const auto& [sum_name, sum_map] : coherent_sums)
        {
            for (const auto& [sum, amp_vector] : coherent_sums[sum_name])
            {                
                csv_file << results.intensity(amp_vector, is_acceptance_corrected).first << ",";
                csv_file << results.intensity(amp_vector, is_acceptance_corrected).second << ",";
            }
        }
        // 5. phase differences
        for (const auto& [pd_name, pd_pair] : phase_diffs)
        {
            csv_file << results.phaseDiff(pd_pair.first, pd_pair.second).first << ",";
            csv_file << results.phaseDiff(pd_pair.first, pd_pair.second).second << ",";
        }
    }
}

// fill all the fit results maps for a single file
void fill_maps(
    FitResults &results,
    std::map<std::string, double> &standard_results,
    std::map<std::string, std::complex<double, double>> &production_coefficients,
    std::map<std::string, std::map<std::string, std::vector<std::string>>> &coherent_sums,
    std::map<std::string, std::pair<std::string, std::string>> &phase_diffs    
    )
{
    // Store the standard AmpTools fit outputs
    standard_results["eMatrixStatus"] = results.eMatrixStatus();
    standard_results["lastMinuitCommandStatus"] = results.lastMinuitCommandStatus();
    standard_results["likelihood"] = results.likelihood();
    standard_results["detected_events"] = results.intensity(false).first;
    standard_results["detected_events_err"] = results.intensity(false).second;
    standard_results["generated_events"] = results.intensity(true).first;
    standard_results["generated_events_err"] = results.intensity(true).second;

    // fill the coherent sum and phase difference maps by iterating over all amps
    for (auto reaction : results.reactionList())
    {
        for (std::string amplitude : results.ampList(reaction))
        {
            // 'amplitude' is the full name stored by AmpTools in the format:
            // "reaction::reflectivitySum::eJPmL"

            // put isotropic background into the single amplitude category
            if (amplitude.find("Bkgd") != std::string::npos ||
                amplitude.find("iso") != std::string::npos)
            {
                coherent_sums["eJPmL"]["Bkgd"].push_back(amplitude);
                continue;
            }            

            // split the "eJPmL" part of the amplitude into its components
            std::string e, JP, m, L;
            std::tie(e, JP, m, L) = parse_amplitude(amplitude);

            // store the production coefficients
            production_coefficients[eJPmL] = results.scaledProductionParameter(amplitude);

            // store the amplitudes in the coherent sum maps
            coherent_sums["eJPmL"][eJPmL].push_back(amplitude);
            coherent_sums["JPmL"][JP + m + L].push_back(amplitude);
            coherent_sums["eJPL"][e + JP + L].push_back(amplitude);
            coherent_sums["JPL"][JP + L].push_back(amplitude);
            coherent_sums["eJP"][e + JP].push_back(amplitude);
            coherent_sums["JP"][JP].push_back(amplitude);
            coherent_sums["e"][e].push_back(amplitude);

            // store the phase differences
            for (std::string pd_amplitude : results.ampList(reaction))
            {
                if (pd_amplitude == amplitude)
                    continue; // don't compare to itself
                // isotropic background cannot have a phase difference
                if (pd_amplitude.find("Bkgd") != std::string::npos ||
                    pd_amplitude.find("iso") != std::string::npos)
                {
                    continue;
                }
                std::string pd_eJPmL = pd_amplitude.substr(pd_amplitude.rfind("::") + 2);

                // avoid duplicates due to reverse ordering of names
                if (phase_diffs.find(pd_eJPmL + "_" + eJPmL) != phase_diffs.end())
                {
                    continue;
                }

                // avoid phase differences between different reflectivities
                if (eJPmL[0] != pd_eJPmL[0])
                {
                    continue;
                }

                phase_diffs[eJPmL + "_" + pd_eJPmL] = std::make_pair(amplitude, pd_amplitude);
            }
        }
    }
}

// grab the "eJPmL" part of the amplitude and split into its components
std::tuple<std::string, std::string, std::string, std::string> parse_amplitude(std::string amplitude)
{
    
    std::string eJPmL = amplitude.substr(amplitude.rfind("::") + 2);
    std::string e, JP, m, L;
    e = eJPmL.substr(0, 1);
    JP = eJPmL.substr(1, 2);
    m = eJPmL.substr(3, 1);
    L = eJPmL.substr(4);
    return std::make_tuple(e, JP, m, L);
}