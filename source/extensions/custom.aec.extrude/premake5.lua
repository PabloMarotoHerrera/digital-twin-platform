local ext = get_current_extension_info()

project_ext(ext)

repo_build.prebuild_link {
    { "custom_aec", ext.target_dir.."/custom_aec" },
}
