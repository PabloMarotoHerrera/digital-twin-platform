local ext = get_current_extension_info()

project_ext(ext)

repo_build.prebuild_link {
    { "dt", ext.target_dir.."/dt" },
}

